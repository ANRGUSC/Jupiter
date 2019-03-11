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

 #ifndef _MR_TRIE
#define _MR_TRIE

#include "Common.h"
#include "Utility.h"

class TrieNode {
 private:
  int level;
  
 public:
  TrieNode( int _level ): level( _level ) {}
  virtual ~TrieNode() {}
  virtual int findPartition( unsigned char* key ) = 0;
  int getLevel() { return level; }
};


class InnerTrieNode: public TrieNode {
 public:
  TrieNode** child;

 public:
 InnerTrieNode( int _level ): TrieNode( _level ) {
    child = new TrieNode*[ 256 ];
  }
  ~InnerTrieNode() {
    for( int i = 0; i < 256; i++ ) {
      delete child[ i ];
    }
    delete [] child;
  }

  int findPartition( unsigned char* key );
  void setChild( int index, TrieNode* _child ) { child[ index ] = _child; }
};

class LeafTrieNode: public TrieNode {
 private:
  int lower;
  int upper;
  PartitionList* partitionList;
  
 public:
 LeafTrieNode( int _level, PartitionList* _partitionList, int _lower, int _upper ): TrieNode( _level ), lower( _lower ), upper( _upper ), partitionList( _partitionList ) {}
  ~LeafTrieNode() {}
  int findPartition( unsigned char* key );
};


class Sorter {
 private:
  unsigned int length;
 public:
 Sorter( unsigned int _length ): length( _length ) {}
  bool operator()( const unsigned char* keyl, const unsigned char* keyr ) { return cmpKey( keyl, keyr, length ); }
};


#endif
