import datetime


class log:
    def _init_(self , title , log):
        '''title輸入標題,log有錯誤訊息打入(無請打入None)'''
        today=datetime.datetime.today()
        time = today.strftime("Time:%Y/%m/%d %H:%M:%S")
        with open("serverlog.txt" , "a+") as f:
            if log == None:
                f.write(f'{time}\nMassage:{title}\n ------------------------------\n')
            else:
                f.write(f'{time}\n Massage:{title}\n [ERROR] {log}\n------------------------------\n')
