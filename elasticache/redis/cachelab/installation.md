Original Source: [Redis](https://redis.io/download)

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


```bash
#Bulk insert command
cat bulk.txt | ./redis-cli --pipe

#Upload to S3
aws s3 cp dump.rdb s3://<bucketname>/
```
