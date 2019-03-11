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

#include "stdio.h"  // printf
#include <iostream>  // cout
#include <iomanip>  // exit()
#include <fstream>  // file handling
#include <string> // string
#include <vector>  // vector<>
using namespace std;
#define MAX_IP_LEN 16
/*
This function converts network monitoring results into IP-value pairs.
The monitoring results is carries by a .txt file.
Each line is of format:
timestamp    srcIP destIP, .... separated by space.

E.g. the input file looks like:

123456:78:10 192.168.1.1 135.246.1.2 123 456
123456:78:20 168.123.01.02 135.246.1.2 123 456
123456:78:30 168.123.01.02 135.468.2.3 579 802


This function extracts the srcIP from each line, make it a key.
The length of the key is the length of the longest IP.
All other IPs will have dummy "."s padded.
This function then adds 10 dummy "*" as its value.

The output is a .txt file. Each line is a key-value pair, separated by space.
The file looks like:

192.168.1.1.. **********
168.123.01.02 **********
168.123.01.02 **********


Key assumptions with hardcoded values as macros:
1. segments of a line are separated by space ' ' 
2. in the input file, the srcIP is the 2nd segment of each line
3. the key value is **********
*/
#define SEP ' '
#define IPLOC 1
#define VALUE "**********"


vector<string> handelLine(string myLine){
    // This function takes a string as the input.
    // The string may contain spaces (i.e., ' ').
    // The function segments the string into several smalle strings
    // based on the spaces.
    // The output is a vector of strings.
    vector<string> sample(1);  // creat a vector of strings, len = 1
    int numSeg = 0;
    int idx = 0;
    for (int i=0; i < myLine.size(); i++){
        if (myLine[i] != SEP){  // the current segment is not completed
            sample[numSeg] += myLine[i];  // add the char to the string
        }
        else{
            numSeg ++;  // current segment completed, move to the next segment
            sample.resize(numSeg + 1);  // increase the vector size by 1
        }
    }
    return sample;
}

vector<vector<string>> handleData(string fileName){
    // This function takes the name of a file (e.g., 'data.txt') as the input.
    // It reads the file line by line.
    // Each line is a string with spaces (i.e., ' ').
    // The function segments each line into several strings based on the spaces. 
    // The output is a 2D matrix. Each row carries the segmented strings
    // of one line.
    ifstream myFile;  // create an object to read the data txt.
    myFile.open(fileName);
    if (!myFile){
        cout << "Unable to open file" << endl;
        exit(1);
    }
    string myLine;  // create an object to read one line of the data
    int numLine = 0;
    // create a 2D matrix with strings as entries
    // each row of this matrix contains all the segments of a line
    vector<vector<string>> samples;
    while (!myFile.eof()){  // while not reaching the end of the file
        if (getline(myFile, myLine)){  // try read a line
            auto sample = handelLine(myLine);
            if (sample.size() > 1){  // skip empty and short lines
                samples.resize(numLine + 1);
                samples[numLine] = sample;
                numLine ++;
            }
        }
    }
    return samples;
}


void extractIPs(string inFileName, string outFileName){
    // each line of the input file has the format of:
    // sth srcIP sth sth ...
    // i.e., the second portion is the IP we want to extract
    cout << "start extract IP" << endl;
    vector<vector<string>> samples = handleData(inFileName);
    ofstream myFile (outFileName);
    int numSamples = samples.size();
    for (int i = 0; i < samples.size(); i ++){
        myFile << samples[i][1];  // the srcIP
        int diff = MAX_IP_LEN - samples[i % samples.size()][IPLOC].size();
        if (diff > 0){  // IP is short, padd some "."s.
            for (int j = 0; j < diff; j++){
                myFile << ".";
            }
        }
        myFile << VALUE;
    }
    cout << "end extract IP" << endl;
}


int main(int argc, char *argv[]){
    if (argc < 3){
        printf("Please tell me both the input and output file names!\n");
    }
    else{
        extractIPs(argv[1], argv[2]);
    }
}

// To compile:
// $ g++ -std=c++11 extractIPs.cpp -o extractIPs
// To run:
// $ ./extractIPs ./Inputs/data.txt
