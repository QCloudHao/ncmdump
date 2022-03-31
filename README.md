# NCM Dump
将网易云会员下载的.ncm音乐文件转换为.mp3或.flac文件

# Usage
```python
python3 ncmdump.py <ncm_folder_path>
# or add '-o' to override
python3 ncmdump.py <ncm_folder_path> -o
```

# NCM struct
Origin from [NCM2MP3](https://github.com/charlotte-xiao/NCM2MP3)
|          信息          |             大小              | 备注                                                         |
| :--------------------: | :---------------------------: | :----------------------------------------------------------- |
|      Magic Header      |           10 bytes            | b'4354454e4644414d' |
|       KEY Length       |            4 bytes            | 用AES128加密RC4密钥后的长度(小端字节排序,无符号整型)         |
| KEY From AES128 Decode | KEY Length(其实就是128 bytes) | 用AES128加密的RC4密钥(注意:1.按字节对0x64异或。2.AES解密(其中PKCS5Padding填充模式会去除末尾填充部分)。3.去除前面`neteasecloudmusic`17个字节。) |
|      Mata Length       |            4 bytes            | Mata的信息的长度(小端字节排序,无符号整型)                    |
|    Mata Data(JSON)     |          Mata Length          | JSON的格式的Mata的信息(注意:1.按字节对0x63异或。2.去除前面`163 key(Don't modify):`22个字节。3.Base64进行decode。4.AES解密;5.去除前面`music:`6个字节后获得JSON。) |
|       CRC校验码        |            4 bytes            | 跳过                                                         |
|          Gap           |            5 bytes            | 跳过                                                         |
|       Image Size       |            4 bytes            | 图片大小                                                     |
|         Image          |          Image Size           | 图片数据                                                     |
|       Music Data       |               -               | RC4-KSA生成s盒,RC4-PRGA解密                                  |
