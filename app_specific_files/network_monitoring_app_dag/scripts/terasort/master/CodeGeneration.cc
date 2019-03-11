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
#include <stdlib.h>
#include <assert.h>
#include <algorithm>

#include "CodeGeneration.h"

using namespace std;

CodeGeneration::CodeGeneration( int _N, int _K, int _R ): N( _N ), K( _K ), R( _R )
{
  NodeSubsetR = generateNodeSubset( R );
  
  if ( N % NodeSubsetR.size() != 0 ) {
    cout << "N is not divisible by [K choose R]\n";
    assert( false );
  }
  Eta = N / NodeSubsetR.size();
  constructM();
  
  // for( int nid = 1; nid <= K; nid++ ) {
  //   NodeImMatrix[ nid ] = generateImMatrix( nid );
  // }
  
  NodeSubsetS = generateNodeSubset( R + 1 );

  for( unsigned int i = 0; i < NodeSubsetS.size(); i++ ) {
    SubsetSIdMap[ NodeSubsetS[ i ] ] = i; 
  }

  for( int nid = 1; nid <= K; nid++ ) {
    NodeSubsetSMap[ nid ] = generateNodeSubsetContain( nid, R + 1 );
  }

  unsigned long fid = 1;
  for( auto nsit = NodeSubsetR.begin(); nsit != NodeSubsetR.end(); nsit++ ) {
    FileNodeMap[ fid ] = *nsit;
    NodeFileMap[ *nsit ] = fid;
    fid++;
  }
}


vector< NodeSet > CodeGeneration::generateNodeSubset( int r )
{
  vector< NodeSet > list;
  vector< NodeSet > ret;
  list.push_back( NodeSet() );
  for( int i = 1; i <= K; i++ ) {
    unsigned int numList = list.size();
    for( unsigned int j = 0; j < numList; j++ ) {
      NodeSet n( list[ j ] );
      n.insert( i );
      if( int( n.size() ) == r ) {
	ret.push_back( n );
      }
      else {
	list.push_back( n );
      }
    }
  }
  return ret;
}


vector< NodeSet > CodeGeneration::generateNodeSubsetContain( int nodeId, int r )
{
  set< int > nodes;
  vector< NodeSet > list;
  vector< NodeSet > ret;

  for( int i = 1; i <= K; i++ ) {
    if( i == nodeId ) {
      NodeSet ns;
      ns.insert( nodeId );
      list.push_back( ns );
      continue;
    }
    nodes.insert( i );
  }

  for( auto nit = nodes.begin(); nit != nodes.end(); nit++ ) {
    int node = *nit;
    unsigned lsize = list.size();
    for( unsigned int i = 0; i < lsize; i++ ) {
      NodeSet ns( list[ i ] );
      ns.insert( node );
      if( ns.size() == (unsigned int) r ) {
	ret.push_back( ns );
      }
      else {
	list.push_back( ns );
      }
    }
  }

  return ret;
}


void CodeGeneration::constructM()
{
  int f = 1;  
  for( auto it = NodeSubsetR.begin(); it != NodeSubsetR.end(); ++it ) {
    NodeSet ns = *it;
    for ( int count = 0; count < Eta; count++ ) {
      for ( auto nit = ns.begin(); nit != ns.end(); ++nit ) {
	int nid = *nit;
	M[ nid ].insert( f );
      }
      f++;
    }
  }
}


ImMatrix CodeGeneration::generateImMatrix( int nid )
{
  InputSet inputs = M[ nid ];
  ImMatrix m( K, vector< bool >( N, false ) );
  for( int q = 1; q <= K; q++ ) {
    for( auto it = inputs.begin(); it != inputs.end(); ++it ) {
      int inputIdx = *it;
      m[ q - 1 ][ inputIdx - 1] = true;
    }
  }
  return m;
}


// void CodeGeneration::generateSubsetDestVpairList()
// {
//   for( auto it = SubsetSIdMap.begin(); it != SubsetSIdMap.end(); ++it ) {
//     NodeSet s = it->first;
//     SubsetSId id = it->second;
//     for( auto kit = s.begin(); kit != s.end(); ++kit ) {
//       int q = *kit;
//       NodeSet t = s;
//       t.erase( q );
//       for( int n = 1; n <= N; n++ ) {
// 	bool exclusive = true;	
// 	if( NodeImMatrix[ q ][ q - 1 ][ n - 1 ] == true ) {
// 	  exclusive = false;
// 	}
// 	else {
// 	  for( auto jit = t.begin(); jit != t.end(); ++jit ) {
// 	    int j = *jit;
// 	    if( NodeImMatrix[ j ][ q - 1 ][ n - 1 ] == false ) {
// 	      exclusive = false;
// 	      break;
// 	    }
// 	  }
// 	}
// 	if( exclusive == true ) {
// 	  SubsetDestVpairList[ id ][ q ].push_back( Vpair( q, n ) );
// 	}
//       }
//     }
//   }
// }


// void CodeGeneration::generateSubsetSrcVjList()
// {
//   for( auto it = SubsetSIdMap.begin(); it != SubsetSIdMap.end(); it++ ) {
//     NodeSet s = it->first;
//     SubsetSId id = it->second;
//     for( auto kit = s.begin(); kit != s.end(); kit++ ) {
//       int k = *kit;
//       NodeSet t = s;
//       t.erase( k );
//       VpairList vpl = SubsetDestVpairList[ id ][ k ];
//       int order = 1;
//       for( auto jit = t.begin(); jit != t.end(); jit++ ) {
// 	int j = *jit;
// 	SubsetSrcVjList[ id ][ j ].push_back( Vj( vpl, k, order ) );
// 	order++;
//       }
//     }
//   }
// }


void CodeGeneration::printNodeSet( NodeSet ns )
{
  cout << '{';
  for( auto nit = ns.begin(); nit != ns.end(); ++nit ) {
    cout << ' ' << *nit;
    if ( nit != --ns.end() ) {
      cout << ',';
    }
  }
  cout << " }";
}


void CodeGeneration::printVpairList( VpairList vpl )
{
  cout << '[';
  for( auto pit = vpl.begin(); pit != vpl.end(); pit++ ) {
    cout << " ( " << pit->first << ", " << pit->second << " )";
    if ( pit != --vpl.end() ) {
      cout << ',';
    }
  }
  cout << " ]";
}


SubsetSId CodeGeneration::getSubsetSId( NodeSet ns )
{
  auto it = SubsetSIdMap.find( ns );
  if( it != SubsetSIdMap.end() ) {
    return it->second;
  }
  else {
    cout << "Cannot find SubsetId\n";
    assert( false );
  }
}
