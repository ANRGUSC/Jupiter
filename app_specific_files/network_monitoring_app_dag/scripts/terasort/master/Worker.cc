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
#include <assert.h>
#include <algorithm>
#include <ctime>

#include "Worker.h"
#include "Configuration.h"
#include "Common.h"
#include "Utility.h"

using namespace std;

Worker::~Worker()
{
  delete conf;
  for ( auto it = partitionList.begin(); it != partitionList.end(); ++it ) {
    delete [] *it;
  }

  LineList* ll = partitionCollection[ rank - 1 ];
  for( auto lit = ll->begin(); lit != ll->end(); lit++ ) {
    delete [] *lit;
  }
  delete ll;
  
  for ( auto it = localList.begin(); it != localList.end(); ++it ) {
     delete [] *it;
  }

  delete trie;
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
    //     std::cout << IPs[i] << " appears: " << counts[i] << " times" << std::endl;
    // }

    // write into a file
    ofstream myFile ("./Output/countIPs.txt");
    for (unsigned int i = 0; i < IPs.size(); i ++){
        myFile << IPs[i] << ' ' << counts[i] << endl;
    }
}

void Worker::run()
{
  // RECEIVE CONFIGURATION FROM MASTER
  conf = new Configuration;
  MPI::COMM_WORLD.Bcast( (void*) conf, sizeof( Configuration ), MPI::CHAR, 0 );


  // RECEIVE PARTITIONS FROM MASTER
  for ( unsigned int i = 1; i < conf->getNumReducer(); i++ ) {
    unsigned char* buff = new unsigned char[ conf->getKeySize() + 1 ];
    MPI::COMM_WORLD.Bcast( buff, conf->getKeySize() + 1, MPI::UNSIGNED_CHAR, 0 );
    partitionList.push_back( buff );
  }


  // EXECUTE MAP PHASE
  clock_t time;
  double rTime;
  execMap();

  
  // SHUFFLING PHASE
  unsigned int lineSize = conf->getLineSize();
  for ( unsigned int i = 1; i <= conf->getNumReducer(); i++ ) {
    if ( i == rank ) {
      clock_t txTime = 0;
      unsigned long long tolSize = 0;
      MPI::COMM_WORLD.Barrier();
      time = clock();  	            
      // Sending from node i
      for ( unsigned int j = 1; j <= conf->getNumReducer(); j++ ) {
	if ( j == i ) {
	  continue;
	}
	TxData& txData = partitionTxData[ j - 1 ];
	txTime -= clock();
	MPI::COMM_WORLD.Send( &( txData.numLine ), 1, MPI::UNSIGNED_LONG_LONG, j, 0 );
	MPI::COMM_WORLD.Send( txData.data, txData.numLine * lineSize, MPI::UNSIGNED_CHAR, j, 0 );
	txTime += clock();
	tolSize += txData.numLine * lineSize + sizeof(unsigned long long);
	delete [] txData.data;
      }
      MPI::COMM_WORLD.Barrier();
      time = clock() - time;
      rTime = double( time ) / CLOCKS_PER_SEC;        
      double txRate = ( tolSize * 8 * 1e-6 ) / ( double( txTime ) / CLOCKS_PER_SEC );
      MPI::COMM_WORLD.Send( &rTime, 1, MPI::DOUBLE, 0, 0 );
      MPI::COMM_WORLD.Send( &txRate, 1, MPI::DOUBLE, 0, 0 );
      //cout << rank << ": Avg sending rate is " << ( tolSize * 8 ) / ( rtxTime * 1e6 ) << " Mbps, Data size is " << tolSize / 1e6 << " MByte\n";
    }
    else {
      MPI::COMM_WORLD.Barrier();
      // Receiving from node i
      TxData& rxData = partitionRxData[ i - 1 ];
      MPI::COMM_WORLD.Recv( &( rxData.numLine ), 1, MPI::UNSIGNED_LONG_LONG, i, 0 );
      rxData.data = new unsigned char[ rxData.numLine * lineSize ];
      MPI::COMM_WORLD.Recv( rxData.data, rxData.numLine*lineSize, MPI::UNSIGNED_CHAR, i, 0 );
      MPI::COMM_WORLD.Barrier();
    }
  }


  // UNPACK PHASE
  time = -clock();
  // append local partition to localList
  for ( auto it = partitionCollection[ rank - 1 ]->begin(); it != partitionCollection[ rank - 1 ]->end(); ++it ) {
    unsigned char* buff = new unsigned char[ conf->getLineSize() ];
    memcpy( buff, *it, conf->getLineSize() );
    localList.push_back( buff );
  }

  // append data from other workers
  for( unsigned int i = 1; i <= conf->getNumReducer(); i++ ) {
    if( i == rank ) {
      continue;
    }
    TxData& rxData = partitionRxData[ i - 1 ];
    for( unsigned long long lc = 0; lc < rxData.numLine; lc++ ) {
      unsigned char* buff = new unsigned char[ lineSize ];
      memcpy( buff, rxData.data + lc*lineSize, lineSize );
      localList.push_back( buff );
    }
    delete [] rxData.data;
  }
  time += clock();
  rTime = double( time ) / CLOCKS_PER_SEC;    
  MPI::COMM_WORLD.Gather( &rTime, 1, MPI::DOUBLE, NULL, 1, MPI::DOUBLE, 0 );      

  
  // REDUCE PHASE
  time = clock();  
  execReduce();
  time = clock() - time;
  rTime = double( time ) / CLOCKS_PER_SEC;    
  MPI::COMM_WORLD.Gather( &rTime, 1, MPI::DOUBLE, NULL, 1, MPI::DOUBLE, 0 );    
  
  outputLocalList();
  //printLocalList();
}


void Worker::execMap()
{
  clock_t time = 0;
  double rTime = 0;
  time -= clock();
  
  // READ INPUT FILE AND PARTITION DATA
  char filePath[ MAX_FILE_PATH ];
  sprintf( filePath, "%s_%d", conf->getInputPath(), rank - 1 );
  ifstream inputFile( filePath, ios::in | ios::binary | ios::ate );
  if ( !inputFile.is_open() ) {
    cout << rank << ": Cannot open input file " << conf->getInputPath() << endl;
    assert( false );
  }

  int fileSize = inputFile.tellg();
  unsigned long int lineSize = conf->getLineSize();
  unsigned long int numLine = fileSize / lineSize;
  inputFile.seekg( 0, ios::beg );

  // Build trie
  unsigned char prefix[ conf->getKeySize() ];
  trie = buildTrie( &partitionList, 0, partitionList.size(), prefix, 0, 2 );

  // Create lists of lines
  for ( unsigned int i = 0; i < conf->getNumReducer(); i++ ) {
    partitionCollection.insert( pair< unsigned int, LineList* >( i, new LineList ) );
  }

  // MAP
  // Put each line to associated collection according to partition list
  for ( unsigned long i = 0; i < numLine; i++ ) {
    unsigned char* buff = new unsigned char[ lineSize ];
    inputFile.read( ( char * ) buff, lineSize );
    unsigned int wid = trie->findPartition( buff );
    partitionCollection.at( wid )->push_back( buff );
  }
  inputFile.close();  
  time += clock();
  rTime = double( time ) / CLOCKS_PER_SEC;  
  MPI::COMM_WORLD.Gather( &rTime, 1, MPI::DOUBLE, NULL, 1, MPI::DOUBLE, 0 );    


  time = -clock();
  // Packet partitioned data to a chunk
  for( unsigned int i = 0; i < conf->getNumReducer(); i++ ) {
    if( i == rank - 1 ) {
      continue;
    }
    unsigned long long numLine = partitionCollection[ i ]->size();
    partitionTxData[ i ].data = new unsigned char[ numLine * lineSize ];
    partitionTxData[ i ].numLine = numLine;
    auto lit = partitionCollection[ i ]->begin();
    for( unsigned long long j = 0; j < numLine * lineSize; j += lineSize ) {
      memcpy( partitionTxData[ i ].data + j, *lit, lineSize );
      delete [] *lit;
      lit++;
    }
    delete partitionCollection[ i ];
  }
  time += clock();
  rTime = double( time ) / CLOCKS_PER_SEC;
  MPI::COMM_WORLD.Gather( &rTime, 1, MPI::DOUBLE, NULL, 1, MPI::DOUBLE, 0 );    
}


void Worker::execReduce()
{
  // if( rank == 1) {
  //   cout << rank << ":Sort " << localList.size() << " lines\n";
  // }
  // stable_sort( localList.begin(), localList.end(), Sorter( conf->getKeySize() ) );
  sort( localList.begin(), localList.end(), Sorter( conf->getKeySize() ) );
}


void Worker::printLocalList()
{
  unsigned long int i = 0;
  for ( auto it = localList.begin(); it != localList.end(); ++it ) {
    cout << rank << ": " << i++ << "| ";
    printKey( *it, conf->getKeySize() );
    cout << endl;
  }
}


void Worker::printPartitionCollection()
{
  for ( auto it = partitionCollection.begin(); it != partitionCollection.end(); ++it ) {
    unsigned int c = it->first;
    LineList* list = it->second;
    unsigned long i = 0;
    for ( auto lit = list->begin(); lit != list->end(); ++lit ) {
      cout << rank << ": " << c << "| " << i++ << "| ";
      printKey( *lit, conf->getKeySize() );
      cout << endl;
    }
  }
}


void Worker::outputLocalList()
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


TrieNode* Worker::buildTrie( PartitionList* partitionList, int lower, int upper, unsigned char* prefix, int prefixSize, int maxDepth )
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
