# known_hosts hash cracking with hashcat

If you just want to know how to use the script, skip to the example usage section below.

## Background

The OpenSSH client uses a file called `known_hosts` to track the fingerprint for previously used ssh servers. This can help the SSH client detect when a man in the middle attack is taking place. If an attacker was to try this attack, the user's client would show a serious warning and refuse to connect. This is done to stop the user from connecting to an attacker's system. In my experience, Ubuntu and Debian servers seem to have the "HashKnownHosts" setting on by default. This setting does not seem to be the defacto default setting, so it may be disabled by the OS or vendor.

in 2005 a team from MIT wrote a [paper](http://nms.csail.mit.edu/projects/ssh/sshworm.pdf) about the potential threat of an SSH based worm. Their theoretical SSH worm would replicate by locating other SSH servers through the known_hosts file. To defend against this threat the OpenSSH team added a new option "HashKnownHosts" in version 4.0. This effectively feature hashes the IP and domains that are stored in the known_hosts file and effectively killed off the threat they had described. However, they did not foresee the GPU password cracking abilities that we have today.

Bruce Schneier also had a [blog post](https://www.schneier.com/blog/archives/2005/05/the_potential_f.html) about the issue and their paper.

Example known_hosts hashing configuration enabled in /etc/ssh/ssh_config:
```shell
    HashKnownHosts yes
```
## The known_hosts file can help Red Teams

During an engagement I ran into a server and network that had detailed network monitoring. I had a shell and I had located a users SSH key. Normally you can read the .bash_history for a given user and see which hosts the user has used ssh to log into, but in this case it seemed the .bash_history file had rolled over. Since there weren't very may ssh commands I decided to try to find a way to crack the hashes in the known_hosts file. Having a list of IP addresses with other SSH servers would be helpful to have, as I wouldn't need to do a noisy network scan to locate them. Also, if an attacker only logs into servers that the admin has already used, there is a good chance this wont raise an alarm and you can stay undetected. 

## known_hosts file format

A non hashed known_hosts file example:
```shell
192.168.10.12 ssh-rsa AAAAB3NzaC1yc2EAAAABIwAAAQEA01yz1a/UkkdKsqNIfALi13OmJ305weWukUtdG5WY2xKBzc3UDqBTVndbpzMEeXl/A/4SAPdc/dUUVNYJWHc8SvcFa2n+NXduq6UPmimJYxX0glHLql9rhX9X6BrpYq93J08tcdPJlS88AF86oL0HRk1l3whN8x7v62UfPSF3/apihx5PQVEYI0rL47wi6gYPRb70CiEn1MCvIJLeyBaIjvhZ+LKsXhNafahGo36Ck7Tf2iqTNuuy56U/ijt0MHg3kOwEecVVbWS3RSASQCfu345BK2a4soeIG1JpfTakz23Cb5T76wBM63uUDvFmmjn+ljZlNafN/AQLwIfYyxQ/pw==
```
a hashed known_hosts example:
```shell
|1|wlPQdgFoYgYsqG6ae20lYopRLPI=|p61txQKmb+Hn49dsD+v0CNuEKd4= ssh-rsa AAAAB3NzaC1yc2EAAAABIwAAAQEAzhZmG33G/3FG3vm0eDdyX1u++i0ceakIkJNgDxVVy6MpodRrpwqXXQj8/OGT
Iwb4YpRXGuL3236IkGugI9GUgFd00UNjMSMt3pqob4hKsEzADl7YfZeV1X7X0b617nze0otdO7TwDMlQ/5KWUwdUoxg50VfpieTzcOpUN/G4J159iKZ41iSF7o4vI+fYisX8y5rJ1BRbt1HO0Gi7w9HZ8tN0B
0glM6JKyoE8TjvbZAeD9PWIWp9JpG1KTY4yXTV1B1CyvtxjRqTMm8mcb+gSGGvv6mSlWCNxJnlXhp91F2GtmgzKsE3FjcMUfkn3c0+P0bKaR8L3GtbyaXJmtDX4xQ==
```
This next example known_hosts file with a single IP address. These commands will explain a little bit more on how these hashes are created (these commands were taken from this [post](https://security.stackexchange.com/questions/56268/ssh-benefits-of-using-hashed-known-hosts)):

First, lets see what is in the known_hosts file:
```shell
$ cat ~/.ssh/known_hosts
|1|GOOqYoIUqAQ4Qsun3Lb9yhEY7bc=|wFUz1PicR/NNbqrgKz4NlClxDdI= ecdsa-sha2-nistp256 AAAAE2V---snip---
```

The first base64 encoded string is used as the salt:
```shell
$ echo -n "GOOqYoIUqAQ4Qsun3Lb9yhEY7bc=" | base64 -d | xxd -p
18e3aa628214a8043842cba7dcb6fdca1118edb7
```

The second string, is the IP address of the server. 
```shell
$ echo -n "192.168.86.245" | openssl sha1 -mac HMAC -macopt hexkey:18e3aa628214a8043842cba7dcb6fdca1118edb7 | awk '{print $2}' | xxd -r -p | base64
wFUz1PicR/NNbqrgKz4NlClxDdI=
```

## My first approach at cracking the known_hosts hashes

I wanted to start off by clarifying that I am not the first to do this attack. I've seen at small handful of posts that describe the technique. This attack also only seems to work if the user logged into the SSH server with the IP address vs. using the domain name.

My first approach with this was to create a cracking dictionary with every possible internal IP address in it ex: 10.0.0.0/8. The file was big, but not unmanageable. the 10.0.0.0/8 private block is around 16 million IP addresses. However, the entire internet would be around 4.3 billion. My first approach worked fairly well, but I found a better way after doing some googling. 

## The optimized approach, mask attacks

I found the following [post](https://hashcat.net/forum/archive/index.php?thread-4762.html) on the hashcat forums with information about using a mask attack for brute-forcing hashes for all IPv4 addresses. Hashcat [mask attacks](https://hashcat.net/wiki/doku.php?id=mask_attack) are used often as they can be better tuned for cracking vs. the brute force method. In our case it is easier to use a mask attack as you don't need to generate a 4.3 billion IP address dictionary file. The IPv4 hcmask file included in this repository was originally downloaded from this [pastebin post](https://pastebin.com/4HQ6C8gG), but I've included it here to save you time. 

## Can OpenSSH find a solution to solve defend against this attack?

It doesn't seem like there would be a clear solution. If they used a more expensive hashing algorithm like bcrypt, the GPUs could still crack the entire IPv4 address space for a single hash in ~50 hours with a single Nvidia 1080 GTX ti. A single card can do about 23223 bcrypt Hashes/second per [this benchmark](https://gist.github.com/epixoip/ace60d09981be09544fdd35005051505) (4,294,967,296 ip addresses / 23223 hashes a second / 60 second per minute / 60 minutes per hour = 51.3 Hours). Also, if bcrypt was used, this could cause slowness or performance issues potentially, especially for lower powered embedded devices.

Edit: I spoke with someone (Aaron) about this attack and he made a good point. If you use IPv6, this attack would be less feasble (read: impossible) for the time being. There are 340,282,366,920,938,463,463,374,607,431,768,211,456 total possible IPv6 addresses.

## Example usage

```shell
#This is an example of what a hashed known_hosts file looks like:
cat ~/.ssh/known_hosts
|1|wlPQdgFoYgYsqG6ae20lYopRLPI=|p61txQKmb+Hn49dsD+v0CNuEKd4= ssh-rsa AAAAB3NzaC1yc2EAA--snip--==

#This will convert the hashed known_hosts file into a format that hashcat can attempt to crack:
python3 kh-converter.py ~/.ssh/known_hosts
a7ad6dc502a66fe1e7e3d76c0febf408db8429de:c253d076016862062ca86e9a7b6d25628a512cf2

#To save the output from kh-converter.py, lets redirect stdout to a file:
python3 kh-converter.py ~/.ssh/known_hosts > converted_known_hosts

#Finally, to crack the "HMAC-SHA1 (key = $salt)" hashes, use the following hashcat command:
hashcat64.bin -m 160 --quiet --hex-salt converted_known_hosts -a 3 ipv4_hcmask.txt 
a7ad6dc502a66fe1e7e3d76c0febf408db8429de:c253d076016862062ca86e9a7b6d25628a512cf2:10.180.6.49
```
As you can see from the hashcat output above, the IP address was found to be `10.180.6.49`. Note: This cracking attempt was completed in about 1 minute on a single Nvidia 1080 GTX GPU.

#### Thanks
Thanks to Jason and Eden for the suggestions on this post.
