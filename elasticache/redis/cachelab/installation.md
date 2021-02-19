```bash
#[Pre Requisite]
yum groupinstall "Development Tools"

#[Download Redis]
wget https://download.redis.io/releases/redis-6.0.10.tar.gz
tar xzf redis-<tab>
cd redis-<tab> 

#[Compile redis]
make distclean 
make 
```
