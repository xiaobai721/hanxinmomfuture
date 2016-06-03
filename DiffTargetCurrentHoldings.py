# -*- coding: cp936 -*-
'''
version: 6
由新浪的url获取期货实时价格，按照交易金额从大到小排列，保证优先交易金额大的合约
yqi, 29, Feb, 2016
'''

from xml.dom import minidom
import time
import pdb
import os
import re
import urllib2

########################
#处理配置文件，得到一些路径
########################
def XmlParse(file_xml):
    dom = minidom.parse(file_xml)
    path_target = dom.getElementsByTagName('target')[0].childNodes[0].nodeValue + time.strftime('%Y%m%d')
    path_current = dom.getElementsByTagName('current')[0].childNodes[0].nodeValue
    path_grouplist = dom.getElementsByTagName('grouplist')[0].childNodes[0].nodeValue
    path_Abandonlist = dom.getElementsByTagName('abandonlist')[0].childNodes[0].nodeValue
    return path_target, path_current, path_grouplist,path_Abandonlist

##############################
#用户来选择用哪个target position
##############################
def ChooseTarget(path_target):
    file_list = []
    nGroup = 0
    all_list = os.listdir(path_target)
    for mlist in all_list:
        if mlist.startswith('LAST_HOLDING'):
            filedir = os.path.join(path_target, mlist)
            if os.path.isfile(filedir):
                file_list.append(mlist)
                tmp_num = int(mlist.split('_')[2])
                if tmp_num > nGroup:
                    nGroup = tmp_num
    file_list_group = []
    for i in range(nGroup):
        file_list_group.append([])  
    for mlist in file_list:
        tmp_num = int(mlist.split('_')[2])
        file_list_group[tmp_num - 1].append(mlist)
    print '文件及对应序号如下：\n'

    i = 1
    for mgroup in file_list_group:
        for mfile in mgroup:
            print '--->>> %d : %s' %(i, mfile)
            i += 1
        print '\n'
    num_file = i
    
    choice_list = []
    print '默认选择文件如下，确定请按\'y\'，并回车。 自己输入请按\'n\'，并回车。'
    for mgroup in file_list_group:
        if mgroup:
            print '%s\n' %mgroup[-1]
            choice_list.append(mgroup[-1])   
    while True:
        sInput = raw_input()
        if 'y' == sInput:
            return choice_list
        elif 'n' == sInput:
            choice_list = []
            print '请输入文件对应编号，多个文件用逗号隔开，按\'回车键\'完成输入。\n'
            while True:
                num_input = raw_input()
                num_list = num_input.split(',')
                if len(set(num_list)) != len(num_list):
                    print '输入序号不能重复，请重新输入'
                else:
                    for mnum in num_list:
                                if mnum.isdigit():
                                    num = int(mnum)
                                    if num <= num_file and num >= 1:
                                        print '%s: %s \n' %(u'选择了文件',file_list[num-1])
                                        choice_list.append(file_list[num-1])
                                    else:
                                        print '输入有误，重新输入 1 至 %d 之间的数字，多个数字用逗号隔开' %num_file
                                else:
                                    print '输入有误，重新输入 1 至 %d 之间的数字，多个数字用逗号隔开' %num_file
                    if len(choice_list) == len(num_list):
                        return choice_list
                    else:
                        print '输入有误，重新输入 1 至 %d 之间的数字，多个数字用逗号隔开' %num_file
        else:
            print '请按 \'y\' 或 \'n\'， 并回车。'
            
#######################            
#处理target position文件
#######################            
def TargetParse(path_target, file_targets):
    tHolding = []
    tInstrument = []
     
    for file_target in file_targets:
        mfile = os.path.join(path_target, file_target)
        rfid = open(mfile, 'r')
        try:
            lines = rfid.readlines()
            for line in lines:
                words = line.split(' ')
                for word in words:
                    if word:
                        try:
                            tmp_quality = int(word[:-1])
                        except Exception,e:
                            tmp_instrument = word
                try:
                    p_tInstrument = tInstrument.index(tmp_instrument)
                    tHolding[p_tInstrument] += tmp_quality
                except Exception,e:
                    tInstrument.append(tmp_instrument)
                    tHolding.append(tmp_quality)
        except Exception, e:
            print '--->>> 打开文件 %s 失败，请关闭程序。'
        finally:
            rfid.close()
                                                
        
    return tInstrument, tHolding

#####################################
#处理持仓文件，得到当前持仓，区分昨今，多空
#####################################
def CurrentParse(file_current):
    cHolding = []
    cInstrument = []
    cInst = []
    
    if os.path.isfile(file_current):
        rfid = open(file_current, 'r')
        try:
            lines = rfid.readlines()
            for line in lines[1:]:
                if line:
                    words = line.split(',')
                    cInst.append(words[0])
                    
                    if 'SPC' in words[0]:
                        continue
                    elif int(words[5]) == 0:#可平量为0
                        continue
                    
                    try:
                        p = cInstrument.index(words[0])
                        cHolding[p][0] = 1 if '买' in words[1] else -1    # 空仓为-1，多仓为1
                        cHolding[p][1] = int(words[4]) + cHolding[p][1]   # 今仓
                        cHolding[p][2] = int(words[3]) + cHolding[p][2]   # 昨仓
                    except Exception,e:
                        cInstrument.append(words[0])
                        tmp = [0] * 3
                        tmp[0] = 1 if '买' in words[1] else -1 # 空仓为-1，多仓为1
                        tmp[1] = int(words[4])                 # 今仓
                        tmp[2] = int(words[3])                 # 昨仓
                        cHolding.append(tmp)
                else:
                    continue
        except Exception, e:
            print e
        finally:
            rfid.close()
    if len(set(cInst)) <> len(cInst):
        print 'SOS SOS SOS! 持仓中有相同正反仓，请检查！'
        print cInst
        
    return cInstrument, cHolding


#####################################
#读取禁止交易品种
#####################################
def Abandon(file_Abandonlist):
    AbInst = []
    rfid = open(file_Abandonlist, 'r')
    try:        
        lines = rfid.readlines()
        if lines == []:
            print 'Abandonlist为空'
            AbInst = []
        else:            
            for line in lines:
                if line :
                    words = line.strip('\n').upper()
                    AbInst.append(filter(str.isalpha, words))
    except Exception, e:
            print '--->>> 打开Abdonlist文件失败，请关闭程序。'
    finally:
            rfid.close()
    return AbInst
	
	
###########################
#读取grouplist文件，来确定系数        
###########################
def GroupParse(file_group):
    Inst = []
    Unit = []

    rfid = open(file_group[0], 'r')
    try:
        lines = rfid.readlines()
        for line in lines:
            if line:
                Inst.append(line[0:-1])
    except Exception, e:
        print e
    finally:
        rfid.close()
    
    rfid = open(file_group[1], 'r')
    try:
        lines = rfid.readlines()
        for line in lines:
            if line:
                tmp = re.match('\d+\s+\d+', line)
                strTmp = tmp.group()
                if strTmp:
                    strSplit = strTmp.split(' ')
                    Unit.append(float((strSplit[-1])))
    except Exception,e:
        print e
    finally:
        rfid.close()
    
    return Inst, Unit

#######################################
#比较target 与 current 持仓，来产生交易的量
#######################################
def DiffTargetCurrent(tInstrument, tHolding, cInstrument, cHolding, Inst, Unit):
    #tmpDiff[0] -> iDiff[1] -> 要交易的量（绝对值）
    #tmpDiff[1] -> iDiff[2] -> 开空
    #tmpDiff[2] -> iDiff[3] -> 开多
    #tmpDiff[3] -> iDiff[4] -> 平昨空
    #tmpDiff[4] -> iDiff[5] -> 平昨多
    #tmpDiff[5] -> iDiff[6] -> 平今空
    #tmpDiff[6] -> iDiff[7] -> 平今多
    #              iDiff[0] -> Money
    
    #在current holding 中找target， 如果没有，说明要开仓
    Diff = []
    for ti in tInstrument:
        tmpDiff = [0] * 7
        if (filter(str.isalpha, ti).upper()) in (Abandon(file_Abandonlist)):
            #print ti
            continue
        else:
            try:
                pt = tInstrument.index(ti)
                pc = cInstrument.index(ti)
                diff = tHolding[pt] - cHolding[pc][0] * (cHolding[pc][1] + cHolding[pc][2])
                tmpDiff[0] = abs(diff)
                # 多仓
                if cHolding[pc][0] > 0:
                        if diff > 0:
                                tmpDiff[2] += diff
                        elif diff < 0:
                                if abs(diff) <= cHolding[pc][2]:
                                        tmpDiff[4] = abs(diff)
                                elif abs(diff) > cHolding[pc][2] and abs(diff) <= cHolding[pc][1] + cHolding[pc][2]:
                                        tmpDiff[4] = cHolding[pc][2]
                                        tmpDiff[6] = abs(diff) - cHolding[pc][2]
                                elif abs(diff) > cHolding[pc][1] + cHolding[pc][2]:
                                        tmpDiff[4] = cHolding[pc][2]
                                        tmpDiff[6] = cHolding[pc][1]
                                        tmpDiff[1] = abs(diff) - cHolding[pc][1] - cHolding[pc][2]
                # 空仓
                elif cHolding[pc][0] < 0:
                        if diff < 0:
                                tmpDiff[1] = abs(diff)
                        elif diff > 0:
                                if diff <= cHolding[pc][2]:
                                        tmpDiff[3] = diff
                                elif diff > cHolding[pc][2] and diff <= cHolding[pc][1] + cHolding[pc][2]:
                                        tmpDiff[3] = cHolding[pc][2]
                                        tmpDiff[5] = diff - cHolding[pc][2]
                                elif diff > cHolding[pc][1] + cHolding[pc][2]:
                                        tmpDiff[3] = cHolding[pc][2]
                                        tmpDiff[5] = cHolding[pc][1]
                                        tmpDiff[2] = diff - cHolding[pc][1] - cHolding[pc][2]
            except Exception,e:
                if tHolding[pt] > 0:
                        tmpDiff[0] = tHolding[pt]
                        tmpDiff[2] = tHolding[pt]
                elif tHolding[pt] < 0:
                        tmpDiff[0] = abs(tHolding[pt])
                        tmpDiff[1] = abs(tHolding[pt])
            tmpDiff.append(ti)
        Diff.append(tmpDiff)

    #在target 中找 current， 如果没有，说明要平仓
    for ci in cInstrument:
        tmpDiff = [0] * 7
        if (filter(str.isalpha, ci).upper()) in Abandon(file_Abandonlist) or 'IC' in ci or 'IF' in ci or 'IH' in ci:
            #print ci
            continue
        else:
            try:
                pt = tInstrument.index(ci)
            except Exception, e:
                pc = cInstrument.index(ci)
                if cHolding[pc][0] > 0:
                    tmpDiff[0] = cHolding[pc][0]
                    tmpDiff[4] = cHolding[pc][2]
                    tmpDiff[6] = cHolding[pc][1]
                elif cHolding[pc][0] < 0:
                    tmpDiff[0] = abs(cHolding[pc][0])
                    tmpDiff[3] = cHolding[pc][2]
                    tmpDiff[5] = cHolding[pc][1]
        tmpDiff.append(ci)
        Diff.append(tmpDiff)
    # 找出Diff中的group，然后找对应的乘数，然后求得总交易额，然后对交易额进行排序
    for iDiff in range(0,len(Diff)):
        Contract = Diff[iDiff][-1].upper()
        try:
            iContract = int(re.search('\d+', Contract).group())
            sContract = re.search('\D+', Contract).group()
            if iContract < 1000:
                iContract += 1000
                Contract = sContract + str(iContract)
            url = r'http://hq.sinajs.cn/list=' + Contract
            Data = urllib2.urlopen(url)
            strData = Data.readlines()
            splitStr = strData[0].split(',')
            price = float(splitStr[8])
        except Exception, e:
            print '--->>> Error, when get price from WEB, contract = %s' %Contract
            return
        
        tmpDiff = []
        tmp = re.match('\D+', Diff[iDiff][-1])
        if tmp:
            mInst = tmp.group()
            try:
                pInst = Inst.index(mInst)
                lots = sum(Diff[iDiff][1:-1])
                money = lots * Unit[pInst] * price / 10000
                Diff[iDiff].insert(0, money)
            except Exception,e:
                print '--->>> Error, when find the group information'
                return
    
    Diff.sort(reverse=True)
    arrow = '--->>>'
    for idiff in Diff:
        flag = True
        if idiff:
            if idiff[1] != 0:
                if idiff[4] != 0:
                    if flag:
                        print '\n%s\t%10.4f万\t%8s' %(arrow, idiff[0], idiff[-1]),
                        flag = False
                    print ',\t买入平仓（平昨空） %3d 手' %idiff[4],                           
                if idiff[5] != 0:
                    if flag:
                        print '\n%s\t%10.4f万\t%8s' %( arrow, idiff[0], idiff[-1]),
                        flag = False
                    print ',\t卖出平仓（平昨多） %3d 手' %idiff[5],
                if idiff[6] != 0:
                    if flag:
                        print '\n%s\t%10.4f万\t%8s' %(arrow, idiff[0], idiff[-1]),
                        flag = False
                    print ',\t买入平今（平今空） %3d 手' %idiff[6],
                if idiff[7] != 0:
                    if flag:
                        print '\n%s\t%10.4f万\t%8s' %(arrow, idiff[0], idiff[-1]),
                        flag = False
                    print ',\t卖出平今（平今多） %3d 手' %idiff[7],
                if idiff[2] != 0:
                    if flag:
                        print '\n%s\t%10.4f万\t%8s' %(arrow, idiff[0], idiff[-1]),
                        flag = False
                    print ',\t卖出开仓（开空） %3d 手' %idiff[2],
                if idiff[3] != 0:
                    if flag:
                        print '\n%s\t%10.4f万\t%8s' %(arrow, idiff[0], idiff[-1]),
                        flag = False
                    print ',\t买入开仓（开多） %3d 手' %idiff[3],
                
                print ''
                
if __name__ == '__main__':
    file_config = r'.\config.xml'
    path_target, path_current, path_grouplist,path_Abandonlist = XmlParse(file_config)

    str_date = time.strftime('%Y%m%d')
    file_target = ChooseTarget(path_target)
    file_current = path_current + str_date + '\\IF_Holdings_tmp.csv'
    file_group = [path_grouplist + 'group.list', path_grouplist + 'group2.list']
    file_Abandonlist = path_Abandonlist + 'Abandonlist.txt'
	
    tInstrument, tHolding = TargetParse(path_target, file_target)
    cInstrument, cHolding = CurrentParse(file_current)

    Inst, Unit = GroupParse(file_group);
   
    DiffTargetCurrent(tInstrument,tHolding, cInstrument, cHolding, Inst, Unit)

    print '\n\n--->>> 按\'回车键\'退出程序.'
    y = raw_input()
