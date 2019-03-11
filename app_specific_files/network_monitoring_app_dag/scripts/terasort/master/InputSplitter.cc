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
#include <assert.h>
#include <cmath>
#include <cstdio>

#include "InputSplitter.h"
#include "Common.h"

using namespace std;

InputSplitter::InputSplitter()
{
  conf = NULL;
  bufferSize = 100000000; //Byte
}

InputSplitter::~InputSplitter()
{

}

void InputSplitter::splitInputFile()
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
  cout << "inputFile " << conf->getInputPath() << " is open\n";

  unsigned int numInput = conf->getNumInput();
  unsigned int LineSize = conf->getLineSize();
  unsigned long long int fileSize = inputFile.tellg();
  unsigned long long int numLine = fileSize / LineSize;

  char* buff = new char[ bufferSize ];
  if ( buff == NULL ) {
    cout << "Cannot allocate buffer for splitting\n";
    assert( false );
  }

  
  // Assume that the number of lines is higher than the number of workers
  assert( numInput <= numLine );

  
  // Split input file equally except the last split that possible includes extra lines
  unsigned long long int splitSize = ( numLine / numInput ) * LineSize;
  unsigned long long int startIndex;
  unsigned long long int endIndex;

  
  // Create split_0, ..., split_(numWorder-2)
  unsigned int i;
  assert( numInput > 1 );
  for ( i = 0; i < (unsigned int) numInput-1; i++ ) {
    startIndex = i * splitSize;
    endIndex = ( i + 1 ) * splitSize - 1;
    createSplit( inputFile, i, startIndex, endIndex, buff );
  }

  
  // Create split_(numInput-1)
  startIndex = ( numInput - 1 ) * splitSize;
  endIndex = fileSize - 1;
  createSplit( inputFile, i, startIndex, endIndex, buff );

  
  // cleanup
  inputFile.close();
  delete [] buff;
}

void InputSplitter::createSplit( ifstream &inputFile, int splitNumber, unsigned long long int startIndex, unsigned long long int endIndex, char* buff )
{
  unsigned long long int currIndex = startIndex;
  unsigned long long int copySize = 0;
  char splitPath[ MAX_FILE_PATH ];  

  // Open splitFile with path name "inputPath_splitNumber"
  sprintf( splitPath, "%s_%d", conf->getInputPath(), splitNumber );
  ofstream splitFile( splitPath, ios::out | ios::binary | ios::trunc );
  if ( !splitFile.is_open() ) {
    cout << "Cannot open split file " << splitPath << endl;
    assert( false );
  }  

  inputFile.seekg( startIndex );
  while ( currIndex <= endIndex ) {
    copySize = min( bufferSize, endIndex - currIndex + 1 );
    inputFile.read( buff, copySize );
    splitFile.write( buff, copySize );
    currIndex += copySize;
  }

  splitFile.close();

  cout << "Create " << splitPath << endl;
}
