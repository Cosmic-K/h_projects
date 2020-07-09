import pandas as pd
import datetime
import glob
import calendar
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np

# scripts to explore HAR open activity dataset

# file_search looks over each file and returns a dataframe
# containing filename user, start/ed times of each days acitvity and date 
# of when activity types are higher than two types 

# overlap_times plots acitivy for each user on weekdays to show time overlaps
# also gets 'useful' users - subsets dataframe by users that have more than 4 days available

# main file uses the meta dataframe of filenames, user, star tand end times to calc the overlapping windows
# and return data fram of acceleraomter data between these windows 
# currently only returns dataframe for user number 7 as they have most days but logic can be expanded in a loop using the
# users as a filter

# data found @ http://lbd.udc.es/research/real-life-HAR-dataset/
# exact data link http://lbd.udc.es/research/real-life-HAR-dataset/data_cleaned_adapted_splits.zip



def file_search():

    # creates lists of accel files in directory 
    # empty lists for loops

    a=[3,1,2,4]
    files = glob.glob('sensoringData_acc_*.csv')
    date_list = []
    user_list = []
    st_list = []
    ed_list = []
    file_list=[]

    col_names = ['file', 'user', 'start_time', 'end_time', 'date']
    
    for file in files:
        # load , drop and change time 

        df = pd.read_csv(file)
        df = df.drop(columns = ['id','acc_x_axis','acc_y_axis','acc_z_axis','activity_id'])
        df['datetime'] = pd.to_datetime(df.timestamp,unit='s',origin='unix')
        df['date'] = df.datetime.dt.date
        
        # remap acvitiy - not really needed anymore bu useful code
        d = dict(zip(df.activity.unique().tolist(), a))
        df = df.replace({'activity':d})
        df = df.drop(columns=['timestamp']) 
        
        users = df.username.unique()

        # loop through users and dates to fund where 'activity is high
        # store lists of files, date, and start and end time

        for user in users:
            temp=df[df['username']==user]
            dates=temp.date.unique()
            for date in dates:
                if len(temp.activity.unique()) > 2:
                    temp_new=temp[temp['date']==date].sort_values(by=['datetime'])
                    user_list.append(user)
                    date_list.append(date)
                    st_list.append(min(temp_new.datetime))
                    ed_list.append(max(temp_new.datetime))
                    file_list.append(file)
    
    d = [file_list, user_list, st_list, ed_list, date_list]
    d = dict(zip(col_names, d))

    df_new = pd.DataFrame(data = d)
    df_new = df_new.sort_values(by=['user', 'date'])
    df_new['duration'] = df_new.end_time - df_new.start_time
    df_new['start_time'] = pd.to_datetime(df_new.start_time)
    df_new['end_time'] = pd.to_datetime(df_new.end_time)
    df_new['start_time'] = df_new.start_time.dt.time
    df_new['end_time'] = df_new.end_time.dt.time
    df_new['day']=[calendar.day_name[i.weekday()] for i in df_new['date']]


    return  df_new


def overlap_times(df, plot= None):

    df_new = df[df['duration'] > datetime.timedelta(hours=6)]
    users = df_new.user.unique()
  
    days = list(df_new.day.unique())
  
    days.remove('Saturday')
    days.remove('Sunday')

    df_new = df_new[df_new.day.isin(days)]

    now = datetime.datetime.now()
    midnight = now.replace(hour=0, minute=0, second=0, microsecond=0)
    mid2 = midnight + datetime.timedelta(hours=23, minutes=59)

    useful_users = []

    # just filters df for number of days and creates plots

    for usr in users:
        temp = df_new[df_new['user']==usr]    
        if len(temp) > 4:
            temp = temp.reset_index(drop=True)   
            useful_users.append(usr)
            if plot:
                fig, ax = plt.subplots(nrows=len(temp), ncols=1, figsize=(15, 15))
                xlim_m=(midnight, mid2)
                plt.setp(ax, xlim=xlim_m)
                for i in range(len(temp)):
                    ax[i].axvspan(datetime.datetime.combine(now, temp['start_time'][i]), datetime.datetime.combine(now, temp['end_time'][i]), alpha=0.5, color='red', label=str(temp['date'][i]))
                    ax[i].set_xlabel('Time (Hours)')
                    ax[i].set_yticklabels([])
                    ax[i].legend()
                    ax[i].xaxis_date()
                    ax[i].xaxis.set_major_formatter(mdates.DateFormatter('%H-%M-%S'))
                    plt.gcf().autofmt_xdate()
                    ax[i].title.set_text(str(temp['day'][i]))
        
                    plt.suptitle('overlapping data_user_' + str(usr))
                    plt.savefig('overlap_weekdays_'+str(usr)+'.png')

    df_new = df_new[df_new.user.isin(useful_users)]
    
    return df_new


def main():

    df_new = file_search()

    df_new  = overlap_times(df_new, plot=None)

    # from plots we kow user 7 has most days
    # so just for user 7 
    # but this could be done in a loop 

    df_new_7 = df_new[df_new['user']==7]
    
    # find overlapping segments of data
    av_duration = df_new_7.duration.mean()
    temp = df_new_7[df_new_7['duration'] > av_duration]
    st_between_dt = max(temp.start_time)
    ed_between_dt = min(temp.end_time)
    ref_dates=temp.date
    file_list = temp.file.tolist()



    df_7_tot = pd.DataFrame([])

    # comprise overlappign segments across files into one dataframe

    for file in file_list:

        df = pd.read_csv(file)
        df = df[df['username']==7]
        df = df.drop(columns = ['id', 'activity_id', 'activity', 'id'])
        df['datetime'] = pd.to_datetime(df.timestamp, unit='s',origin='unix')
        df['date'] = df.datetime.dt.date
        df['time'] = df.datetime.dt.time
        df = df[df.date.isin(ref_dates)]
        df['accel_res'] = np.sqrt(df.acc_x_axis**2 + df.acc_y_axis**2 + df.acc_z_axis**2)
        df = df.set_index(df.datetime)
        df = df.between_time(st_between_dt, ed_between_dt)
        df = df.drop(columns=['timestamp'])
        df_7_tot = df_7_tot.append(df) 
    
    return df_7_tot
          
        # take std every min 
        # binarise based on std value 