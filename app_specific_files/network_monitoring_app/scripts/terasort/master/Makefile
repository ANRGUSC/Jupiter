CC = mpic++
CFLAGS = -std=c++11 -Wall
DFLAGS = -std=c++11 -Wall -ggdb

all: TeraSort CodedTeraSort Splitter InputPlacement
clean:
	rm -f *.o
	rm -f TeraSort CodedTeraSort Splitter Codegen BroadcastTest InputPlacement

cleanclean: clean
	rm -f ./Input/*_*
	rm -f ./Output/*_*
	rm -f ./Tmp/*
	rm -f *.*~
	rm -f *~




TeraSort: main.o Master.o Worker.o Trie.o Utility.o PartitionSampling.o 
	$(CC) $(CFLAGS) -o TeraSort main.o Master.o Worker.o Trie.o Utility.o PartitionSampling.o

CodedTeraSort: CodedMain.o CodedMaster.o CodedWorker.o Trie.o Utility.o PartitionSampling.o CodeGeneration.o
	$(CC) $(CFLAGS) -o CodedTeraSort CodedMain.o CodedMaster.o CodedWorker.o Trie.o Utility.o PartitionSampling.o CodeGeneration.o

Splitter: InputSplitter.o Configuration.h CodedConfiguration.h
	$(CC) $(CFLAGS) -o Splitter Splitter.cc InputSplitter.o

InputPlacement: InputPlacement.cc CodeGeneration.o Configuration.h CodedConfiguration.h
	$(CC) $(CFLAGS) -o InputPlacement InputPlacement.cc CodeGeneration.o

Trie.o: Trie.cc Trie.h
	$(CC) $(CFLAGS) -c Trie.cc

PartitionSampling.o: PartitionSampling.cc PartitionSampling.h Configuration.h
	$(CC) $(CFLAGS) -c PartitionSampling.cc

Utility.o: Utility.cc Utility.h
	$(CC) $(CFLAGS) -c Utility.cc

InputSplitter.o: InputSplitter.cc InputSplitter.h Configuration.h CodedConfiguration.h
	$(CC) $(CFLAGS) -c InputSplitter.cc

CodeGeneration.o: CodeGeneration.cc CodeGeneration.h
	$(CC) $(CFLAGS) -c CodeGeneration.cc



main.o: main.cc Configuration.h
	$(CC) $(CFLAGS) -c main.cc

Master.o: Master.cc Master.h Configuration.h
	$(CC) $(CFLAGS) -c Master.cc

Worker.o: Worker.cc Worker.h Configuration.h
	$(CC) $(CFLAGS) -c Worker.cc




CodedMain.o: CodedMain.cc CodedConfiguration.h
	$(CC) $(CFLAGS) -c CodedMain.cc

CodedMaster.o: CodedMaster.cc CodedMaster.h CodedConfiguration.h
	$(CC) $(CFLAGS) -c CodedMaster.cc

CodedWorker.o: CodedWorker.cc CodedWorker.h CodedConfiguration.h
	$(CC) $(CFLAGS) -c CodedWorker.cc
