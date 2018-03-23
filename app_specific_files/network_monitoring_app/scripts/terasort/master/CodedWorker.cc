/**
 * Copyright (c) 2018, Autonomous Networks Research Group. All rights reserved.
 * Developed by:
 * Autonomous Networks Research Group (ANRG)
 * University of Southern California
 * http://anrg.usc.edu/
 *
 * Contributors:
 * Pranav Sakulkar, 
 * Pradipta Ghosh, 
 * Aleksandra Knezevic, 
 * Jiatong Wang, 
 * Quynh Nguyen, 
 * Jason Tran, 
 * H.V. Krishna Giri Narra, 
 * Zhifeng Lin, 
 * Songze Li, 
 * Ming Yu, 
 * Bhaskar Krishnamachari, 
 * Salman Avestimehr, 
 * Murali Annavaram
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy 
 * of this software and associated documentation files (the "Software"), to deal
 * with the Software without restriction, including without limitation the 
 * rights to use, copy, modify, merge, publish, distribute, sublicense, and/or 
 * sell copies of the Software, and to permit persons to whom the Software is 
 * furnished to do so, subject to the following conditions:
 * - Redistributions of source code must retain the above copyright notice, this
 *     list of conditions and the following disclaimers.
 * - Redistributions in binary form must reproduce the above copyright notice, 
 *     this list of conditions and the following disclaimers in the 
 *     documentation and/or other materials provided with the distribution.
 * - Neither the names of Autonomous Networks Research Group, nor University of 
 *     Southern California, nor the names of its contributors may be used to 
 *     endorse or promote products derived from this Software without specific 
 *     prior written permission.
 * - A citation to the Autonomous Networks Research Group must be included in 
 *     any publications benefiting from the use of the Software.
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR 
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, 
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE 
 * CONTRIBUTORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER 
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS WITH 
 * THE SOFTWARE.
 */

 #include <iostream>
#include <mpi.h>
#include <iomanip>
#include <fstream>
#include <cstdio>
#include <map>
#include <unordered_map>
#include <assert.h>
#include <algorithm>
#include <ctime>
#include <string.h>
#include <cstdint>

#include "CodedWorker.h"
#include "CodedConfiguration.h"
#include "Common.h"
#include "Utility.h"
#include "CodeGeneration.h"

using namespace std;

CodedWorker::~CodedWorker()
{
  for ( auto it = partitionList.begin(); it != partitionList.end(); ++it ) {
    delete [] *it;
  }

  // Delete from inputPartitionCollection
  InputSet inputSet = cg->getM( rank );
  for ( auto init = inputSet.begin(); init != inputSet.end(); init++ ) {
    unsigned int inputId = *init;
    LineList* list = inputPartitionCollection[ inputId ][ rank - 1 ];
    for ( auto lit = list->begin(); lit != list->end(); lit++ ) {
      delete [] *lit;
    }
    delete list;
  }  

  // Delete from encodePreData
  for ( auto it = encodePreData.begin(); it != encodePreData.end(); it++ ) {
    DataPartMap dp = it->second;
    for ( auto it2 = dp.begin(); it2 != dp.end(); it2++ ) {
      vector< DataChunk >& vdc = it2->second;
      for ( auto dcit = vdc.begin(); dcit != vdc.end(); dcit++ ) {
	delete [] dcit->data;
      }
    }
  }

  // Delete from localList
  for ( auto it = localList.begin(); it != localList.end(); ++it ) {
     delete [] *it;
  }

  delete trie;    
  delete cg;
  delete conf;
}

void countFrequency(vector<unsigned char *> locaList){
    // initialize
    int lenIP = 16;
    vector<string> IPs(1);
    vector<int> counts(1);
    IPs[0].resize(lenIP);
    copy(locaList[0], locaList[0] + lenIP, IPs[0].begin());
    int numIPs = 0;  // the actual number of different IPs - 1

    // count frequency
    for (unsigned int i = 0; i < locaList.size(); i++){
            string ip(locaList[i], locaList[i] + lenIP);
            if (ip.compare(IPs[numIPs]) != 0){  // find a new IP
                numIPs ++;
                IPs.resize(numIPs + 1);
                IPs[numIPs].resize(lenIP);
                counts.resize(numIPs + 1);
                copy(locaList[i], locaList[i] + lenIP, IPs[numIPs].begin());
            }
            counts[numIPs] ++;
    }
    // for (int i = 0; i < numIPs + 1; i++){
    //     cout << IPs[i] << " appears: " << counts[i] << " times" << endl;
    // }

    // write into a file
    ofstream myFile ("./Output/countIPs-C.txt");
    for (unsigned int i = 0; i < IPs.size(); i ++){
        myFile << IPs[i] << ' ' << counts[i] << endl;
    }
}

void CodedWorker::run()
{
  // RECEIVE CONFIGURATION FROM MASTER
  conf = new CodedConfiguration;
  MPI::COMM_WORLD.Bcast( (void*) conf, sizeof( CodedConfiguration ), MPI::CHAR, 0 );


  // RECEIVE PARTITIONS FROM MASTER
  for ( unsigned int i = 1; i < conf->getNumReducer(); i++ ) {
    unsigned char* buff = new unsigned char[ conf->getKeySize() + 1 ];
    MPI::COMM_WORLD.Bcast( buff, conf->getKeySize() + 1, MPI::UNSIGNED_CHAR, 0 );
    partitionList.push_back( buff );
  }

  clock_t time;
  double rTime;  

  
  // GENERATE CODING SCHEME AND MULTICAST GROUPS
  time = clock();
  cg = new CodeGeneration( conf->getNumInput(), conf->getNumReducer(), conf->getLoad() );
  genMulticastGroup();
  time = clock() - time;
  rTime = double( time ) / CLOCKS_PER_SEC;
  MPI::COMM_WORLD.Gather( &rTime, 1, MPI::DOUBLE, NULL, 1, MPI::DOUBLE, 0 );    

  
  // EXECUTE MAP PHASE
  time = clock();
  execMap();
  time = clock() - time;
  rTime = double( time ) / CLOCKS_PER_SEC;  
  MPI::COMM_WORLD.Gather( &rTime, 1, MPI::DOUBLE, NULL, 1, MPI::DOUBLE, 0 );      


  // EXECUTE ENCODING PHASE
  time = clock();
  execEncoding();
  time = clock() - time;
  rTime = double( time ) / CLOCKS_PER_SEC;
  MPI::COMM_WORLD.Gather( &rTime, 1, MPI::DOUBLE, NULL, 1, MPI::DOUBLE, 0 );      


  // // START PARALLEL DECODE 
  // // maxDecodeJob = ( cg->getNodeSubsetS().size() * ( cg->getR() * ( cg->getR() + 1 ) ) ) / cg->getK();
  // // int tid = pthread_create( &decodeThread, NULL, parallelDecoder, (void*) this );
  // // if( tid ) {
  // //   cout << rank << ": ERROR -- cannot create parallel decoder thread\n";
  // //   assert( false );
  // // }

  
  // SHUFFLING PHASE
  //time = clock();
  execShuffle();
  //time = clock() - time;
  //cout << rank << ": Shuffle phase takes " << double( time ) / CLOCKS_PER_SEC << " seconds.\n";


  // EXECUTE DECODING PHASE
  time = clock();
  execDecoding();
  time = clock() - time;
  rTime = double( time ) / CLOCKS_PER_SEC;
  MPI::COMM_WORLD.Gather( &rTime, 1, MPI::DOUBLE, NULL, 1, MPI::DOUBLE, 0 );      

  // // // WAIT UNTIL PARALLEL DECODING IS DONE
  // // time = clock();  
  // // pthread_join( decodeThread, NULL );
  // // time = clock() - time;
  // // cout << rank << ": Additional decoding phase takes " << double( time ) / CLOCKS_PER_SEC << " seconds.\n";    


  // REDUCE PHASE
  time = clock();
  execReduce();
  time = clock() - time;
  rTime = double( time ) / CLOCKS_PER_SEC;  
  MPI::COMM_WORLD.Gather( &rTime, 1, MPI::DOUBLE, NULL, 1, MPI::DOUBLE, 0 );
  
  outputLocalList();
  //printLocalList();
}


unsigned int CodedWorker::findAssociatePartition( const unsigned char* line )
{
  unsigned int i;
  for ( i = 0 ; i < partitionList.size(); i++ ) {
    if ( cmpKey( line, partitionList.at( i ), conf->getKeySize() ) == true ) {
      return i;
    }
  }
  return i;
}


void CodedWorker::execMap()
{
  // Get a set of inputs to be processed
  InputSet inputSet = cg->getM( rank );

  // Build trie
  unsigned char prefix[ conf->getKeySize() ];
  trie = buildTrie( &partitionList, 0, partitionList.size(), prefix, 0, 2 );

  // Read input files and partition data
  for ( auto init = inputSet.begin(); init != inputSet.end(); init++ ) {
    unsigned int inputId = *init;

    // Read input
    char filePath[ MAX_FILE_PATH ];
    sprintf( filePath, "%s_%d", conf->getInputPath(), inputId - 1 );
    ifstream inputFile( filePath, ios::in | ios::binary | ios::ate );
    if ( !inputFile.is_open() ) {
      cout << rank << ": Cannot open input file " << filePath << endl;
      assert( false );
    }

    unsigned long fileSize = inputFile.tellg();
    unsigned long int lineSize = conf->getLineSize();
    unsigned long int numLine = fileSize / lineSize;
    inputFile.seekg( 0, ios::beg );
    PartitionCollection& pc = inputPartitionCollection[ inputId ];

    // Crate lists of lines
    for ( unsigned int i = 0; i < conf->getNumReducer(); i++ ) {
      pc[ i ] = new LineList;
      // inputPartitionCollection[ inputId ][ i ] = new LineList;
    }
    
    // Partition data in the input file
    for ( unsigned long i = 0; i < numLine; i++ ) {
      unsigned char* buff = new unsigned char[ lineSize ];
      inputFile.read( ( char * ) buff, lineSize );
      unsigned int wid = trie->findPartition( buff );
      pc[ wid ]->push_back( buff );      
      // inputPartitionCollection[ inputId ][ wid ]->push_back( buff );
    }

    // Remove unnecessarily lists (partitions associated with the other nodes having the file)
    NodeSet fsIndex = cg->getNodeSetFromFileID( inputId );
    for ( unsigned int i = 0; i < conf->getNumReducer(); i++ ) {
      if( i + 1 != rank && fsIndex.find( i + 1 ) != fsIndex.end() ) {
	LineList* list = pc[ i ];
	// LineList* list = inputPartitionCollection[ inputId ][ i ];
	for ( auto lit = list->begin(); lit != list->end(); lit++ ) {
	  delete [] *lit;
	}
	delete list;	
      }
    }

    inputFile.close();
  }

  //writeInputPartitionCollection();
}


void CodedWorker::execEncoding()
{
  vector< NodeSet > subsetS = cg->getNodeSubsetSContain( rank );
  unsigned lineSize = conf->getLineSize();
  for( auto nsit = subsetS.begin(); nsit != subsetS.end(); nsit++ ) {
    SubsetSId nsid = cg->getSubsetSId( *nsit );
    unsigned long long maxSize = 0;
    
    // Construct chucks of input from data with index ns\{q}
    for( auto qit = nsit->begin(); qit != nsit->end(); qit++ ) {
      if( (unsigned int) *qit == rank ) {
	continue;
      }
      int destId = *qit;      
      NodeSet inputIdx( *nsit );
      inputIdx.erase( destId );
      
      unsigned long fid = cg->getFileIDFromNodeSet( inputIdx );
      VpairList vplist;      
      vplist.push_back( Vpair( destId, fid ) );
      
      unsigned int partitionId = destId - 1;
      
      LineList* ll = inputPartitionCollection[ fid ][ partitionId ];

      auto lit = ll->begin();
      unsigned int numPart = conf->getLoad();
      unsigned long long chunkSize = ll->size() / numPart; // a number of lines ( not bytes )
      // first chunk to second last chunk
      for( unsigned int ci = 0; ci < numPart - 1; ci++ ) {
	unsigned char* chunk = new unsigned char[ chunkSize * lineSize ];
	for( unsigned long long j = 0; j < chunkSize; j++ ) {
	  memcpy( chunk + j * lineSize, *lit, lineSize );
	  lit++;
	}
	DataChunk dc;
	dc.data = chunk;
	dc.size = chunkSize;
	encodePreData[ nsid ][ vplist ].push_back( dc );
      }
      // last chuck
      unsigned long long lastChunkSize = ll->size() - chunkSize * ( numPart - 1 );      
      unsigned char* chunk = new unsigned char[ lastChunkSize * lineSize ];
      for( unsigned long long j = 0; j < lastChunkSize; j++ ) {
	memcpy( chunk + j * lineSize, *lit, lineSize );
	lit++;
      }
      DataChunk dc;
      dc.data = chunk;
      dc.size = lastChunkSize;
      encodePreData[ nsid ][ vplist ].push_back( dc );

      // Determine associated chunk of a worker ( order in ns )
      unsigned int rankChunk = 0;  // in [ 0, ... , r - 1 ]
      for( auto it = inputIdx.begin(); it != inputIdx.end(); it++ ) {
	if( (unsigned int) *it == rank ) {
	  break;
	}
	rankChunk++;
      }
      maxSize = max( maxSize, encodePreData[ nsid ][ vplist ][ rankChunk ].size );

      // Remode unused intermediate data from Map
      for( auto lit = ll->begin(); lit != ll->end(); lit++ ) {
	delete [] *lit;
      }
      delete ll;
    }

    // Initialize encode data
    encodeDataSend[ nsid ].data = new unsigned char[ maxSize * lineSize ](); // Initial it with 0
    encodeDataSend[ nsid ].size = maxSize;
    unsigned char* data = encodeDataSend[ nsid ].data;

    // Encode Data
    for( auto qit = nsit->begin(); qit != nsit->end(); qit++ ) {
      if( (unsigned int) *qit == rank ) {
	continue;
      }
      int destId = *qit;      
      NodeSet inputIdx( *nsit );
      inputIdx.erase( destId );
      unsigned long fid = cg->getFileIDFromNodeSet( inputIdx );
      VpairList vplist;
      vplist.push_back( Vpair( destId, fid ) );

      // Determine associated chunk of a worker ( order in ns )
      unsigned int rankChunk = 0;  // in [ 0, ... , r - 1 ]
      for( auto it = inputIdx.begin(); it != inputIdx.end(); it++ ) {
	if( (unsigned int) *it == rank ) {
	  break;
	}
	rankChunk++;
      }
      
      // Start encoding
      unsigned char* predata = encodePreData[ nsid ][ vplist ][ rankChunk ].data;
      unsigned long long size = encodePreData[ nsid ][ vplist ][ rankChunk ].size;
      unsigned long long maxiter = size * lineSize / sizeof( uint32_t );
      for( unsigned long long i = 0; i < maxiter; i++ ) {
	( ( uint32_t* ) data )[ i ] ^= ( ( uint32_t* ) predata )[ i ];
      }

      // Fill metadata
      MetaData md;
      md.vpList = vplist;
      md.vpSize[ vplist[ 0 ] ] = size; // Assume Eta = 1;
      md.partNumber = rankChunk + 1;
      md.size = size; 
      encodeDataSend[ nsid ].metaList.push_back( md );
    }

    // Serialize Metadata
    EnData& endata = encodeDataSend[ nsid ];
    unsigned int ms = 0;
    ms += sizeof( unsigned int ); // metaList.size()
    for ( unsigned int m = 0; m < endata.metaList.size(); m++ ) {
      ms += sizeof( unsigned int ); // vpList.size()
      ms += sizeof( int ) * 2 * endata.metaList[ m ].vpList.size(); // vpList
      ms += sizeof( unsigned int ); // vpSize.size()
      ms += ( sizeof( int ) * 2 + sizeof( unsigned long long ) ) * endata.metaList[ m ].vpSize.size(); // vpSize
      ms += sizeof( unsigned int ); // partNumber
      ms += sizeof( unsigned long long ); // size
    }
    encodeDataSend[ nsid ].metaSize = ms;

    unsigned char* mbuff = new unsigned char[ ms ];
    unsigned char* p = mbuff;
    unsigned int metaSize = endata.metaList.size();
    memcpy( p, &metaSize, sizeof( unsigned int ) );
    p += sizeof( unsigned int );
    // meta data List
    for ( unsigned int m = 0; m < metaSize; m++ ) {
      MetaData mdata = endata.metaList[ m ];
      unsigned int numVp = mdata.vpList.size();
      memcpy( p, &numVp, sizeof( unsigned int ) );
      p += sizeof( unsigned int );
      // vpair List
      for ( unsigned int v = 0; v < numVp; v++ ) {
	memcpy( p, &( mdata.vpList[ v ].first ), sizeof( int ) );
	p += sizeof( int );
	memcpy( p, &( mdata.vpList[ v ].second ), sizeof( int ) );
	p += sizeof( int );
      }
      // vpair size Map
      unsigned int numVps = mdata.vpSize.size();
      memcpy( p, &numVps, sizeof( unsigned int ) );
      p += sizeof( unsigned int );
      for ( auto vpsit = mdata.vpSize.begin(); vpsit != mdata.vpSize.end(); vpsit++ ) {
	Vpair vp = vpsit->first;
	unsigned long long size = vpsit->second;
	memcpy( p, &( vp.first ), sizeof( int ) );
	p += sizeof( int );
	memcpy( p, &( vp.second ), sizeof( int ) );
	p += sizeof( int );
	memcpy( p, &size, sizeof( unsigned long long ) );
	p += sizeof( unsigned long long );
      }
      memcpy( p, &( mdata.partNumber ), sizeof( unsigned int ) );
      p += sizeof( unsigned int );
      memcpy( p, &( mdata.size ), sizeof( unsigned long long ) );
      p += sizeof( unsigned long long );
    }
    encodeDataSend[ nsid ].serialMeta = mbuff;
  }
}


void CodedWorker::execShuffle()
{
  // SUBSET-BY-SUBSET
  // *** If it is to be used, need to fix ns to nsid.
  // vector< NodeSet > subsetList = cg->getNodeSubsetS();
  // for( auto nsit = subsetList.begin(); nsit != subsetList.end(); nsit++ ) {
  //   NodeSet ns = *nsit;
  //   MPI::Intracomm mcComm = multicastGroupMap[ ns ];
  //   unsigned int rootId = 0;
  //   for( auto nit = ns.begin(); nit != ns.end(); nit++ ) {
  //     mcComm.Barrier();      
  //     if( (unsigned int)( rank ) == (unsigned int)( *nit ) ) {
  // 	// Active Node
  // 	sendEncodeData( encodeDataSend[ ns ], mcComm );	
  //     }
  //     else {
  // 	if( ns.find( rank ) != ns.end() ) {
  // 	  // Receive Node
  // 	  recvEncodeData( ns, rootId, mcComm );
  // 	}
  // 	else {
  // 	  // Do nothing
  // 	}

  //     }
  //     rootId++;
  //     mcComm.Barrier();
  //   }
  // }


  // NODE-BY-NODE
  clock_t time;
  //map< NodeSet, SubsetSId > ssmap = cg->getSubsetSIdMap();
  for ( unsigned int activeId = 1; activeId <= conf->getNumReducer(); activeId++ ) {
    unsigned long long tolSize;
    clock_t txTime;
    workerComm.Barrier();
    if ( rank == activeId ) {
      time = clock();
      txTime = 0;
      tolSize = 0;
    }
    vector< NodeSet >& vset = cg->getNodeSubsetSContain( activeId );
    //for( auto nsit = ssmap.begin(); nsit != ssmap.end(); nsit++ ) {
    for( auto nsit = vset.begin(); nsit != vset.end(); nsit++ ) {
      // NodeSet ns = nsit->first;
      // SubsetSId nsid = nsit->second;
      NodeSet ns = *nsit;
      SubsetSId nsid = cg->getSubsetSId( ns );

      // Ignore subset that does not contain the activeId
      if ( ns.find( activeId ) == ns.end() ) {
  	continue;
      }

      MPI::Intracomm mcComm = multicastGroupMap[ nsid ];
      if ( rank == activeId ) {
	txTime -= clock();
  	sendEncodeData( encodeDataSend[ nsid ], mcComm );
	txTime += clock();
	EnData& endata = encodeDataSend[ nsid ];
	tolSize += ( endata.size * conf->getLineSize() ) + endata.metaSize + ( 2 * sizeof(unsigned long long ) );
      }
      else if ( ns.find( rank ) != ns.end() ) {
  	//convert activeId to rootId of a particular multicast group
  	unsigned int rootId = 0;
  	for( auto nid = ns.begin(); nid != ns.end(); nid++ ) {
  	  if( (unsigned int)(*nid) == activeId ) {
  	    break;
  	  }
  	  rootId++;	  
  	}
  	recvEncodeData( nsid, rootId, mcComm );
      }
    }

    // Active node should stop timer here
    workerComm.Barrier();        
    if ( rank == activeId ) {
      time = clock() - time;
      double rTime = double( time ) / CLOCKS_PER_SEC;
      double txRate = ( tolSize * 8 * 1e-6 ) / ( double( txTime ) / CLOCKS_PER_SEC );
      MPI::COMM_WORLD.Send( &rTime, 1, MPI::DOUBLE, 0, 0 );
      MPI::COMM_WORLD.Send( &txRate, 1, MPI::DOUBLE, 0, 0 );      
      //cout << rank  << ": Avg sending rate is " << ( tolSize * 8 ) / ( rtxTime * 1e6 ) << " Mbps, Data size is " << tolSize / 1e6 << " MByte\n";
    }
  }
}


void CodedWorker::execDecoding()
{
  for( auto nsit = encodeDataRecv.begin(); nsit != encodeDataRecv.end(); nsit++ ) {
    SubsetSId nsid = nsit->first;
    vector< EnData >& endataList = nsit->second;
    for( auto eit = endataList.begin(); eit != endataList.end(); eit++ ) {
      EnData& endata = *eit;
      unsigned char* cdData = endata.data;
      unsigned long long cdSize = endata.size;
      vector< MetaData >& metaList = endata.metaList;

      unsigned int numDecode = 0;
      // Decode per VpairList
      MetaData dcMeta;
      for( auto mit = metaList.begin(); mit != metaList.end(); mit++ ) {
	MetaData& meta = *mit;
	if( encodePreData[ nsid ].find( meta.vpList ) == encodePreData[ nsid ].end() ) {
 	  dcMeta = meta;
	  // No original data for decoding;
	  continue;
	}
	unsigned char* oData = encodePreData[ nsid ][ meta.vpList ][ meta.partNumber - 1 ].data;
	unsigned long long oSize = encodePreData[ nsid ][ meta.vpList ][ meta.partNumber - 1 ].size;
	unsigned long long maxByte = min( oSize, cdSize ) * conf->getLineSize();
	unsigned long long maxIter = maxByte / sizeof( uint32_t );
	for( unsigned long long i = 0; i < maxIter; i++ ) {
	  ((uint32_t*) cdData )[ i ] ^= ((uint32_t*) oData )[ i ];
	}
	numDecode++;
      }

      // sanity check
      if( numDecode != metaList.size() - 1 ) {
	cout << rank << ": Decode error " << numDecode << '/' << metaList.size() - 1 << endl;
	assert( numDecode != metaList.size() - 1 );
      }

      if( decodePreData[ nsid ][ dcMeta.vpList ].empty() ) {
      	for( unsigned int i = 0; i < conf->getLoad(); i++ ) {
      	  decodePreData[ nsid ][ dcMeta.vpList ].push_back( DataChunk() );
      	}
      }

      decodePreData[ nsid ][ dcMeta.vpList ][ dcMeta.partNumber - 1].data = cdData;
      decodePreData[ nsid ][ dcMeta.vpList ][ dcMeta.partNumber - 1].size = dcMeta.size;
    }
  }


  unsigned int partitionId = rank - 1;
  unsigned int lineSize = conf->getLineSize();  

  // Get partitioned data from input files, already stored in memory.
  InputSet inputSet = cg->getM( rank );
  for( auto init = inputSet.begin(); init != inputSet.end(); init++ ) {
    unsigned int inputId = *init;
    LineList* ll = inputPartitionCollection[ inputId ][ partitionId ];
    // copy line by line
    for( auto lit = ll->begin(); lit != ll->end(); lit++ ) {
      unsigned char* buff = new unsigned char[ lineSize ];
      memcpy( buff, *lit, lineSize );
      localList.push_back( buff );
    }
    localLoadSet.insert( inputId );
  }

  // Get partitioned data from other workers
  for( auto nvit = decodePreData.begin(); nvit != decodePreData.end(); nvit++ ) {
    DataPartMap& dpMap = nvit->second;
    for( auto vvit = dpMap.begin(); vvit != dpMap.end(); vvit++ ) {
      VpairList vplist = vvit->first;
      vector< DataChunk > vdc = vvit->second;
      // Add inputId to localLoadSet
      for( auto vpit = vplist.begin(); vpit != vplist.end(); vpit++ ) {
  	localLoadSet.insert( vpit->second );
      }
      // Add data from each part to locallist
      for( auto dcit = vdc.begin(); dcit != vdc.end(); dcit++ ) {
  	unsigned char* data = dcit->data;
  	for( unsigned long long i = 0; i < dcit->size; i++ ) {
  	  unsigned char* buff = new unsigned char[ lineSize ];
  	  memcpy( buff, data + i*lineSize, lineSize );
  	  localList.push_back( buff );	  	  
  	}
  	delete [] dcit->data;
      }
    }
  }
  
  if( localLoadSet.size() != conf->getNumInput() ) {
    cout << rank << ": Only have paritioned data from ";
    CodeGeneration::printNodeSet( localLoadSet );
    cout << endl;
    assert( false );
  }    
}


// PARALLEL DECODE THREAD FUNCTION
// void* CodedWorker::parallelDecoder( void* pthis )
// {
//   CodedWorker* parent = ( CodedWorker* ) pthis;
  
//   unsigned long maxNumJob = parent->maxDecodeJob;
//   while( maxNumJob > 0 ) {
//     // decode from queue
//     if( parent->decodeQueue.empty() ) {
//       continue;
//     }
    
//     DecodeJob job = parent->decodeQueue.front();
//     parent->decodeQueue.pop();
//     SubsetSId& nsid = job.sid;
//     EnData& endata = job.endata;
//     LineList* cdData = endata.data;
//     vector< MetaData >& metaList = endata.metaList;

//     unsigned int numDecode = 0;
//     // Decode per VpairList
//     MetaData dcMeta;
//     for( auto mit = metaList.begin(); mit != metaList.end(); mit++ ) {
//       MetaData& meta = *mit;
//       if( parent->encodePreData[ nsid ].find( meta.vpList ) == parent->encodePreData[ nsid ].end() ) {
// 	dcMeta = meta;
// 	// No original data for decoding;
// 	continue;
//       }
//       LineList* oData = parent->encodePreData[ nsid ][ meta.vpList ][ meta.partNumber - 1 ];
//       auto cdlit = cdData->begin();
//       auto olit = oData->begin();
//       while( cdlit != cdData->end() && olit != oData->end() ) {
// 	// 4-Byte by 4-Byte decoding
// 	// This assumes that line size is divisible by 4
// 	unsigned int maxIter = parent->conf->getLineSize() / sizeof( uint32_t );
// 	for( unsigned int i = 0; i < maxIter; i++ ) {
// 	  ((uint32_t*) *cdlit)[ i ] ^= ((uint32_t*) *olit)[ i ];
// 	}

	
// 	cdlit++;
// 	olit++;
//       }
//       numDecode++;
//     }

//     // sanity check
//     if( numDecode != metaList.size() - 1 ) {
//       cout << parent->rank << ": Decode error " << numDecode << '/' << metaList.size() - 1 << endl;
//       assert( numDecode != metaList.size() - 1 );
//     }

//     // Trim decoded data back to its original data size
//     while( cdData->size() > dcMeta.size ) {
//       cdData->pop_back();
//     }
      
//     if( parent->decodePreData[ nsid ][ dcMeta.vpList ].empty() ) {
//       for( unsigned int i = 0; i < parent->conf->getLoad(); i++ ) {
// 	parent->decodePreData[ nsid ][ dcMeta.vpList ].push_back( NULL );
//       }
//     }

//     parent->decodePreData[ nsid ][ dcMeta.vpList ][ dcMeta.partNumber - 1] = cdData;    
//     maxNumJob--;
//     cout << parent->rank << ": maxNumjob " << maxNumJob << endl;
//   }

//   return NULL;
// }


void CodedWorker::execReduce()
{  
  // if( rank == 1) {
  //   cout << rank << ":Sort " << localList.size() << " lines\n";
  // }
  // stable_sort( localList.begin(), localList.end(), Sorter( conf->getKeySize() ) );
  sort( localList.begin(), localList.end(), Sorter( conf->getKeySize() ) );
}



void CodedWorker::sendEncodeData( CodedWorker::EnData& endata, MPI::Intracomm& comm )
{
  // Send actual data
  unsigned lineSize = conf->getLineSize();  
  int rootId = comm.Get_rank();
  comm.Bcast( &( endata.size ), 1, MPI::UNSIGNED_LONG_LONG, rootId );
  comm.Bcast( endata.data, endata.size*lineSize, MPI::UNSIGNED_CHAR, rootId );
  delete [] endata.data;

  // Send serialized meta data
  comm.Bcast( &( endata.metaSize ), 1, MPI::UNSIGNED_LONG_LONG, rootId ); 
  comm.Bcast( endata.serialMeta, endata.metaSize, MPI::UNSIGNED_CHAR, rootId );
  delete [] endata.serialMeta;
}


void CodedWorker::recvEncodeData( SubsetSId nsid, unsigned int rootId, MPI::Intracomm& comm )
{
  EnData endata;
  unsigned lineSize = conf->getLineSize();

  // Receive actual data
  comm.Bcast( &( endata.size ), 1, MPI::UNSIGNED_LONG_LONG, rootId );
  endata.data = new unsigned char[ endata.size * lineSize ];
  comm.Bcast( endata.data, endata.size*lineSize, MPI::UNSIGNED_CHAR, rootId );

  // Receive serialized meta data
  comm.Bcast( &( endata.metaSize ), 1, MPI::UNSIGNED_LONG_LONG, rootId );
  endata.serialMeta = new unsigned char[ endata.metaSize ];
  comm.Bcast( ( unsigned char* ) endata.serialMeta, endata.metaSize, MPI::UNSIGNED_CHAR, rootId );

  // De-serialized meta data
  unsigned char* p = endata.serialMeta;
  unsigned int metaNum;
  memcpy( &metaNum, p, sizeof( unsigned int ) );
  p += sizeof( unsigned int );
  // meta data List  
  for ( unsigned int m = 0; m < metaNum; m++ ) {
    MetaData mdata;
    // vpair List
    unsigned int numVp;
    memcpy( &numVp, p, sizeof( unsigned int ) );
    p += sizeof( unsigned int );
    for ( unsigned int v = 0; v < numVp; v++ ) {
      Vpair vp;
      memcpy( &( vp.first ), p, sizeof( int ) );
      p += sizeof( int );
      memcpy( &( vp.second ), p, sizeof( int ) );
      p += sizeof( int );
      mdata.vpList.push_back( vp );
    }
    // VpairSize Map
    unsigned int numVps;
    memcpy( &numVps, p, sizeof( unsigned int ) );
    p += sizeof( unsigned int );
    for ( unsigned int vs = 0; vs < numVps; vs++ ) {
      Vpair vp;
      unsigned long long size;
      memcpy( &( vp.first ), p, sizeof( int ) );
      p += sizeof( int );
      memcpy( &( vp.second ), p, sizeof( int ) );
      p += sizeof( int );
      memcpy( &size, p, sizeof( unsigned long long ) );
      p += sizeof( unsigned long long );
      mdata.vpSize[ vp ] = size;
    }
    memcpy( &( mdata.partNumber ), p, sizeof( unsigned int ) );
    p += sizeof( unsigned int );
    memcpy( &( mdata.size ), p, sizeof( unsigned long long ) );
    p += sizeof( unsigned long long );
    endata.metaList.push_back( mdata );
  }
  delete [] endata.serialMeta;

  //Serial decoder
  encodeDataRecv[ nsid ].push_back( endata );
}


void CodedWorker::genMulticastGroup()
{
  map< NodeSet, SubsetSId > ssmap = cg->getSubsetSIdMap();
  for( auto nsit = ssmap.begin(); nsit != ssmap.end(); nsit++ ) {
    NodeSet ns = nsit->first;
    SubsetSId nsid = nsit->second;
    int color = ( ns.find( rank ) != ns.end() ) ? 1 : 0;
    MPI::Intracomm mgComm = workerComm.Split( color, rank );
    multicastGroupMap[ nsid ] = mgComm;
  }
}


void CodedWorker::printLocalList()
{
  unsigned long int i = 0;
  for ( auto it = localList.begin(); it != localList.end(); ++it ) {
    cout << rank << ": " << i++ << "| ";
    printKey( *it, conf->getKeySize() );
    cout << endl;
  }
}


void CodedWorker::writeInputPartitionCollection()
{
  char buff[ MAX_FILE_PATH ];
  sprintf( buff, "./Tmp/InputPartitionCollection_%u", rank );
  ofstream outf( buff, ios::out | ios::binary | ios::trunc );
  InputSet inputSet = cg->getM( rank );  
  for ( auto init = inputSet.begin(); init != inputSet.end(); init++ ) {
    unsigned int inputId = *init;
    PartitionCollection& pc = inputPartitionCollection[ inputId ];
    for ( auto pit = pc.begin(); pit != pc.end(); pit++ ) {
      unsigned int parId = pit->first;
      LineList* list = pit->second;
      sprintf( buff, ">> Input %u, Partition %u <<", inputId, parId );
      outf.write( buff, strlen( buff ) );
      for ( auto lit = list->begin(); lit != list->end(); lit++ ) {
	outf.write( ( char * ) *lit, conf->getLineSize() );
      }
    }
  }
  outf.close();
  cout << rank << ": InputPartitionCollection is saved.\n";
}


void CodedWorker::outputLocalList()
{
  char buff[ MAX_FILE_PATH ];
  sprintf( buff, "%s_%u", conf->getOutputPath(), rank - 1 );
  ofstream outputFile( buff, ios::out | ios::binary | ios::trunc );
  for ( auto it = localList.begin(); it != localList.end(); ++it ) {
    outputFile.write( ( char* ) *it, conf->getLineSize() );
  }
  outputFile.close();
  if (localList.size() > 0){
    countFrequency(localList);
  }
  //cout << rank << ": outputFile " << buff << " is saved.\n";
}


TrieNode* CodedWorker::buildTrie( PartitionList* partitionList, int lower, int upper, unsigned char* prefix, int prefixSize, int maxDepth )
{
  if ( prefixSize >= maxDepth || lower == upper ) {
    return new LeafTrieNode( prefixSize, partitionList, lower, upper );
  }
  InnerTrieNode* result = new InnerTrieNode( prefixSize );
  int curr = lower;
  for ( unsigned char ch = 0; ch < 255; ch++ ) {
    prefix[ prefixSize ] = ch;
    lower = curr;
    while( curr < upper ) {
      if( cmpKey( prefix, partitionList->at( curr ), prefixSize + 1 ) ) {
	break;
      }
      curr++;
    }
    result->setChild( ch, buildTrie( partitionList, lower, curr, prefix, prefixSize + 1, maxDepth ) );
  }
  prefix[ prefixSize ] = 255;
  result->setChild( 255, buildTrie( partitionList, curr, upper, prefix, prefixSize + 1, maxDepth ) );
  return result;
}
