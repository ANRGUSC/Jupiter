## Main Jupiter Scripts

When building docker containers using a build_push_*.py script,
`apt-get install` may fail because an apt repository is decomissioned. Add the
`--no-cache` flag to the `docker build` system call in the python script to
rebuild a container from scratch.