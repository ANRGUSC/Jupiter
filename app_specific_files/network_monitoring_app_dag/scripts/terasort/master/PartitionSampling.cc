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
#include <fstream>
#include <algorithm>
#include <iomanip>
#include <cmath>
#include <assert.h>
#include <string.h>

#include "PartitionSampling.h"
#include "Common.h"

using namespace std;

PartitionSampling::PartitionSampling()
{
  conf = NULL;
}

PartitionSampling::~PartitionSampling()
{
  
}

PartitionList* PartitionSampling::createPartitions()
{  
  if ( !conf ) {
    cout << "Configuration has not been provided.\n";
    assert( false );
  }

  ifstream inputFile( conf->getInputPath(), ios::in | ios::binary | ios::ate );
  if ( !inputFile.is_open() ) {
    cout << "Cannot open input file " << conf->getInputPath() << endl;
    assert( false );
  }

  PartitionList keyList;
  long unsigned int keySize = conf->getKeySize();
  unsigned long fileSize = inputFile.tellg();
  long unsigned int numSamples = min( conf->getNumSamples(), fileSize / conf->getLineSize() );

  
  // Sample keys
  inputFile.seekg( 0 );
  long unsigned int gapSkip = ( ( fileSize / conf->getLineSize() ) / numSamples - 1 ) * conf->getLineSize();
  for ( long unsigned int i = 0; i < numSamples; i++ ) {
    unsigned char *keyBuff = new unsigned char [ keySize + 1 ];
    if ( keyBuff == NULL ) {
      cout << "Cannot allocate memory to sample keys.\n";
      assert( false );
    }
    inputFile.read( (char *) keyBuff, keySize );            
    keyBuff[ keySize ] = '\0';
    keyList.push_back( keyBuff );
    inputFile.seekg( conf->getValueSize() + gapSkip , ios_base::cur );
  }
  inputFile.close();
  
    
  // Sort sampled keys
  stable_sort( keyList.begin(), keyList.end(), cmpKey );
  
  // Partition keys
  PartitionList* partitions = new PartitionList;
  long unsigned int numPartitions = conf->getNumReducer();
  long unsigned int sizePartition = round( numSamples / numPartitions );
  for ( unsigned long int i = 1; i < numPartitions; i++ ) {
    unsigned char *keyBuff = new unsigned char [ keySize + 1 ];
    if ( keyBuff == NULL ) {
      cout << "Cannot allocate memory for partition keys.\n";
      assert( false );
    }
    memcpy( keyBuff, keyList.at( i * sizePartition ), keySize + 1 );
    partitions->push_back( keyBuff );
  }

  // The partition list will be broadcast
  // Save partitions to partition list file
  // ofstream partitionFile( conf->getPartitionPath(), ios::out | ios::binary | ios::trunc );
  // for ( auto k = partitions->begin(); k != partitions->end(); ++k ) {
  //   partitionFile.write( (char *) *k, keySize );
  // }
  // partitionFile.close();
  
  // Clean up
  for ( auto k = keyList.begin(); k != keyList.end(); ++k ) {
    delete [] (*k);
  }

  return partitions;
}


bool PartitionSampling::cmpKey( const unsigned char* keyl, const unsigned char* keyr )
{
  for ( unsigned long i = 0; keyl[i] != '\0'; i++ ) {
    if ( keyl[ i ] < keyr[ i ] ) {
      return true;
    }
    else if ( keyl[ i ] > keyr[ i ] ) {
      return false;
    }
  }
  return true;
}


void PartitionSampling::printKeys( const PartitionList& keyList ) const
{
  unsigned long int i = 0;
  for ( auto k = keyList.begin(); k != keyList.end(); ++k ) {
    cout << "Key " << dec << i << ": ";
    for ( unsigned long int j = 0; j < conf->getKeySize(); j++ ) {
      cout << setw( 2 ) << setfill( '0' ) << hex << (int) (*k)[j] << " ";
    }
    cout << dec << endl;
    i++;
  }  
}
