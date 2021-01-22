# -*-coding:utf-8 -*-
'''
@file    :   logicTest.py
@time    :   2021/01/22 11:32:53
@author  :   宋义深 
@version :   1.0
@contact :   1371033826@qq.com 
@license :   GPL-3.0 License
@link    :   https://github.com/Eason010212/EasonMQTT
'''

import Decoders, Encoders, definition
def logicTest():
    '''
        报文解析的逻辑测试。请复制到src文件夹下进行测试。
    '''
    print(Decoders.CONNECT_Decoder(Encoders.CONNECT_Encoder(1,0,1,2,1,0,256,'eason0212','is','ijsfs','eason')))
    print(Decoders.CONNACK_Decoder(Encoders.CONNACK_Encoder(1,definition.ConnackReturnCode.REFUSED_ILLEGAL_CLIENTID)))
    print(Decoders.PUBLISH_Decoder(Encoders.PUBLISH_Encoder(1,2,1,'hhh',10,'hhhhh')))
    print(Decoders.PUBACK_Decoder(Encoders.PUBACK_Encoder(10)))
    print(Decoders.PUBREC_Decoder(Encoders.PUBREC_Encoder(10)))
    print(Decoders.PUBREL_Decoder(Encoders.PUBREL_Encoder(10)))
    print(Decoders.PUBCOMP_Decoder(Encoders.PUBCOMP_Encoder(10)))
    print(Decoders.SUBSCRIBE_Decoder(Encoders.SUBSCRIBE_Encoder(11,[{'topic':'2333','qos':1},{'topic':'2433','qos':2}])))
    print(Decoders.SUBACK_Decoder(Encoders.SUBACK_Encoder(11,[0,128])))
    print(Decoders.UNSUBSCRIBE_Decoder(Encoders.UNSUBSCRIBE_Encoder(12,['2333','2433','2533'])))
    print(Decoders.UNSUBACK_Decoder(Encoders.UNSUBACK_Encoder(12)))
    print(Decoders.PINGREQ_Decoder(Encoders.PINGREQ_Encoder()))
    print(Decoders.PINGRESP_Decoder(Encoders.PINGRESP_Encoder()))
    print(Decoders.DISCONNECT_Decoder(Encoders.DISCONNECT_Encoder()))

logicTest()