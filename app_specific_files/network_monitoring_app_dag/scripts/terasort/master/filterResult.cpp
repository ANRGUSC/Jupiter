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

/*
This function sorts the frequency of keys in descending order.

E.g., input file input.txt looks like:

192.168.1.1.. 1
168.123.01.02 2

which means the the 1st IP (192.168.1.1..) appeared once, the 2nd IP (168.123.01.02) appeared twice.

After sorting, the output result.txt looks like:

192.168.1.1.. 1
168.123.01.02 2

*/


// C++ program for implementation of Heap Sort
// The sort is in descending order.
// Reference:
// https://www.tutorialspoint.com/cplusplus/cpp_return_arrays_from_functions.htm 

void heapify(vector<int> &vec, vector<int> &idx, int n, int i)
{
    int smallest = i;  // Initialize largest as root
    int l = 2 * i + 1;  // left = 2*i + 1
    int r = 2 * i + 2;  // right = 2*i + 2
 
    // If left child is larger than root
    if (l < n && vec[l] < vec[smallest])
        smallest = l;
 
    // If right child is larger than largest so far
    if (r < n && vec[r] < vec[smallest])
        smallest = r;
 
    // If largest is not root
    if (smallest != i)
    { 
        swap(vec[i], vec[smallest]);
        swap(idx[i], idx[smallest]);
 
        // Recursively heapify the affected sub-tree
        heapify(vec, idx, n, smallest);
    }
}
 
// main function to do heap sort
// It will return the order of the sorting
// E.g., if vec = [12, 56, 23], then return idx = [1, 2, 0]
vector<int> heapSort(vector<int> &vec)
{   
    int n = int(vec.size());
    vector<int> idx(vec.size());
    for (int i = 0; i < n; i++)
        idx[i] = i;
    // Build heap (revecange vector)
    for (int i = n / 2 - 1; i >= 0; i--)
        heapify(vec, idx, n, i);
    // One by one extract an element from heap
    for (int i = n - 1; i >= 0; i--)
    {
        // Move current root to end
        swap(vec[0], vec[i]);
        swap(idx[0], idx[i]);
        heapify(vec, idx, i, 0);
    }
    return idx;
}


void sortResult(string inFileName, string outFileName){
    vector<string> IPs;
    vector<int> counts;
    int numIPs = 0;
    // read files
    ifstream myFile;  // create an object to read the data txt.
    myFile.open(inFileName);
    string myLine;
    while (!myFile.eof()){  // while not reaching the end of the file
        if (getline(myFile, myLine)){  // try read a line
            IPs.resize(numIPs + 1);
            unsigned int loc = 0;
            // read IP
            while (myLine[loc] != ' ' && loc < myLine.size()){
                IPs[numIPs] += myLine[loc];
                loc ++;
            }
            // read the count
            string freq;
            while (loc < myLine.size()){
                freq += myLine[loc];
                loc ++;
            }
            counts.resize(numIPs + 1);
            counts[numIPs] = atoi(freq.c_str());
            numIPs ++;
        }
    }
    // sort the counts
    auto idx = heapSort(counts);  // sort counts, and return idx
    ofstream outFile (outFileName);
    for (int i = 0; i < numIPs; i++){
        outFile << IPs[idx[i]] << ' ' << counts[i] << endl;
    }
}

void filterResult(string inFileName, string outFileName, int thres){
    int numIPs = 0;
    // read files
    ifstream myFile;  // create an object to read the data txt.
    myFile.open(inFileName);
    ofstream outFile (outFileName);
    string myLine;
    while (!myFile.eof()){  // while not reaching the end of the file
        if (getline(myFile, myLine)){  // try read a line
            // read the IP
            string IP;
            unsigned int loc = 0;
            // read IP
            char previous = '1';
            while (myLine[loc] != ' ' && loc < myLine.size()){
                // remove pending dots
                if (!(previous == '.' && myLine[loc] == '.')){
                   IP += myLine[loc];
                }
                previous = myLine[loc];
                loc ++;
            }
            IP.pop_back();  // remove the last dot
            // read the count
            string freq;
            while (loc < myLine.size()){
                freq += myLine[loc];
                loc ++;
            }
            if (atoi(freq.c_str()) >= thres){
                outFile << IP << endl;
            }
        }
    }
}

int main(int argc, char *argv[]){
    if (argc < 3){
        printf("Please tell me both the input and output file names!\n.");
    }
    else{
        if (argc == 3)
        {
            printf("filtering the IPs with a threshold of 50\n");
            filterResult(argv[1], argv[2], 50);
        }
        else{
            filterResult(argv[1], argv[2], atoi(argv[3]));
        }
    }
}
