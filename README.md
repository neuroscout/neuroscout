# neuroscout ⚜

To set up docker, ensure docker, docker-compose (and if on OSX) docker-machine or docker for mac are installed.

First create a docker-machine and point Docker to it:
    docker-machine create -d virtualbox dev;
    eval "$(docker-machine env dev)"
    
Or skip this step if using "Docker for Mac"

Next, build the containers and start the services:
     docker-compose build
     docker-compose up -d

The server should now be running. Navigate to the docker-machine's ip (docker-machine ip dev) or localhost if on Docker for Mac
