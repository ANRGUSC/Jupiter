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

 #ifndef _MR_CONFIGURATION
#define _MR_CONFIGURATION

class Configuration {

 protected:
  unsigned int numReducer;
  unsigned int numInput;  
  
  const char *inputPath;
  const char *outputPath;
  const char *partitionPath;
  unsigned long numSamples;
  
 public:
  Configuration() {
    numReducer = 3;
    numInput = numReducer;    
    
    inputPath = "./Intermediate/srcIPs.txt";
    outputPath = "./Output/Output";
    partitionPath = "./Partition/Partition";
    numSamples = 10000;
  }
  ~Configuration() {}
  const static unsigned int KEY_SIZE = 16;
  const static unsigned int VALUE_SIZE = 10;  
  
  unsigned int getNumReducer() const { return numReducer; }
  unsigned int getNumInput() const { return numInput; }  
  const char *getInputPath() const { return inputPath; }
  const char *getOutputPath() const { return outputPath; }
  const char *getPartitionPath() const { return partitionPath; }
  unsigned int getKeySize() const { return KEY_SIZE; }
  unsigned int getValueSize() const { return VALUE_SIZE; }
  unsigned int getLineSize() const { return KEY_SIZE + VALUE_SIZE; }
  unsigned long getNumSamples() const { return numSamples; }  
};

#endif
