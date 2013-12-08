#include <algorithm>
#include <map>
#include <stdlib.h>
#include <cstdlib>
#include <stdio.h>
#include <iostream>
#include <string.h>
#include <sys/types.h>    // socket, bind
#include <sys/socket.h>   // socket, bind, listen, inet_ntoa
#include <netinet/in.h>   // htonl, htons, inet_ntoa
#include <arpa/inet.h>    // inet_ntoa
#include <netdb.h>        // gethostbyname
#include <unistd.h>       // read, write, close
#include <string.h>       // bzero
#include <netinet/tcp.h>  // SO_REUSEADDR
#include <sys/uio.h>      // writev
#include <signal.h>
#include <fcntl.h>
#include <sys/time.h>
#include <string>
#include <vector>
#include <cstring>

#define BUFSIZE 100
#define TIMEOUT 600  // timeout once every 10 minutes

using namespace std;

// ---------------------------
// main

int main(int argc, char** argv) {


    int clientSd;
    int error = -1;
    vector<string> addrs; // store addresses to give out to peers
    map<string, long> timeoutMap;


    char* buf = (char*) malloc(BUFSIZE);
    struct timeval currentTime;



    // read command line parameters
    sockaddr_in acceptSockAddr;
    bzero((char*) &acceptSockAddr, sizeof (acceptSockAddr));
    acceptSockAddr.sin_family = AF_INET;
    acceptSockAddr.sin_addr.s_addr = htonl(INADDR_ANY);
    acceptSockAddr.sin_port = htons(21168);

    int serverSd = socket(AF_INET, SOCK_STREAM, 0);

    // bind serverSd to socket
    bind(serverSd, (sockaddr*) & acceptSockAddr, sizeof (acceptSockAddr));
    listen(serverSd, 100); // start listening to port

    sockaddr_in newSockAddr; // sockaddr_in for accepting connection
    socklen_t newSockAddrSize = sizeof (newSockAddr);
    while (1) {
        cout << "about to accept... " << endl;
        clientSd = accept(serverSd, (sockaddr *) & newSockAddr, &newSockAddrSize); // waits until connection
        cout << "waiting... " << endl;
        int byte_count = recv(clientSd, (char*) buf, BUFSIZE, 0);
        cout << "data size: " << byte_count << endl;
        // got an op code -- 0 is register, 1 is discover, 2 is remove, 3 is for keepalive
        buf[byte_count] = '\0'; // add null character at the end
        cout << "got data: " << buf << endl;
        char* pch; // = (char*) malloc(BUFSIZE);
        // do some string tokenization.  All our parameters are separated by colons
        pch = strtok(buf, ":");
        int command = atoi(pch); // first parameter is the command code
        pch = strtok(NULL, ":"); // this is our next parameter
        char* str = (char*) malloc(BUFSIZE);
        int n = 3;
        int port = -1;
        char* intStr = (char*) malloc(6); // port numbers will be 5 characters or less
        std::string sendString;
        if (command != 3) { // if this isn't a keepalive, delete anything that is out of date
            // do a lazy delete
            gettimeofday(&currentTime, NULL);
            for (std::map<string, long>::iterator it = timeoutMap.begin(); it != timeoutMap.end(); ++it) {
                if (currentTime.tv_sec > it->second) { // current time is past the timeout
                    cout << it->first << " timed out" << endl;
                    vector<string>::iterator it2 = std::find(addrs.begin(), addrs.end(), it->first);
                    if (it2 != addrs.end()) {
                        cout << "erased from address list" << endl;
                        addrs.erase(it2);
                    }
                    timeoutMap.erase(it);

                }
            }

            // std::cout << it->first << " => " << it->second << '\n';
        }
        switch (command) {
            case 0: // register
                if (pch != NULL) {
                    port = atoi(pch);
                }

                cout << "adding " << pch << endl;
                // now get it back and print it
                inet_ntop(AF_INET, &(newSockAddr.sin_addr), str, INET_ADDRSTRLEN);
                sprintf(intStr, ",%d\n", port);
                str = strcat(str, intStr);
                // logic to not add addrs that already exist
                if (std::find(addrs.begin(), addrs.end(), str) == addrs.end()) {

                    addrs.push_back(str);
                    gettimeofday(&currentTime, NULL);
                    timeoutMap.insert(std::pair<string, long>(str, (currentTime.tv_sec + TIMEOUT)));
                    cout << "added " << str << endl;
                } else {
                    cout << "address is already in list" << endl;
                }
                break;
            case 1: //   get some peers

                int numPeers;
                if (pch != NULL) {
                    numPeers = atoi(pch);
                } else {
                    numPeers = 3;
                }
                cout << "requesting peers" << endl;
                if (addrs.size() > numPeers) { // we have enough peers to satisfy the request
                    for (int i = 0; i < numPeers; i++) {
                        int v = rand() % addrs.size();
                        //cout << "sending - " << addrs[v].c_str() << endl;
                        //cout << "size = " << strlen(addrs[v].c_str()) << endl;
                        //send(clientSd, addrs[v].c_str(), strlen(addrs[v].c_str()), 0);
                        sendString.append(addrs[v].c_str());
                    }
                    cout << "sent peers" << endl;
                } else { // just give the entire list since we don't have enough peers to satisfy the request
                    for (vector<string>::iterator iter = addrs.begin(); iter != addrs.end(); iter++) {
                        //cout << "sending - " << (*iter).c_str() << endl;
                        //cout << "size = " << strlen((*iter).c_str()) << endl;
                        //send(clientSd, (*iter).c_str(), strlen((*iter).c_str()), 0);
                        sendString.append((*iter).c_str());
                    }
                }

                cout << "sending - " << sendString << endl;
                cout << "size = " << strlen(sendString.c_str()) << endl;
                send(clientSd, sendString.c_str(), strlen(sendString.c_str()), 0);

                cout << "sent peers" << endl;

                break;
            case 2: // remove yourself from the list

                if (pch != NULL) {
                    port = atoi(pch);
                }


                cout << "removing peers" << endl;
                inet_ntop(AF_INET, &(newSockAddr.sin_addr), str, INET_ADDRSTRLEN);

                sprintf(intStr, ",%d\n", port);
                str = strcat(str, intStr);
                // go through the list an find the peer to remove
                for (vector<string>::iterator iter = addrs.begin(); iter != addrs.end(); iter++) {
                    cout << "test" << endl;
                    if ((*iter).compare(str) == 0) {
                        cout << "erase!" << endl;
                        addrs.erase(iter);
                        break;
                    }
                }
                // also remove from timeout list
                timeoutMap.erase(str);

                cout << "removed " << str << endl;
                break;

            case 3:
                if (pch != NULL) {
                    port = atoi(pch);
                }


                cout << "keep alive" << endl;
                inet_ntop(AF_INET, &(newSockAddr.sin_addr), str, INET_ADDRSTRLEN);

                sprintf(intStr, ",%d\n", port);
                str = strcat(str, intStr);

                gettimeofday(&currentTime, NULL);
                // add some additional time to currentVal
                timeoutMap[str] = (currentTime.tv_sec + TIMEOUT); // convert tv_sec & tv_usec to millisecond


                cout << "kept alive " << str << endl;
                break;

                // got something that I couldn't figure out how to use
            default:
                cout << "fail! " << buf << endl;
                //  send(clientSd, (char*) &error, sizeof error, 0);
        }

        cout << "closing" << endl;
        cout << "status = " << close(clientSd) << endl;
        free(intStr);
        free(str);
        //        free(pch);
    }
    free(buf);
    return 0;

}
