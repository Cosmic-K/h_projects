import pandas as pd 
import ast
import string
import calendar
import datetime
import matplotlib.pyplot as plt
import numpy as np
import matplotlib.dates as mdates
import seaborn as sb

# script to explore open source smart phone data found on kaggle 
# here: https://www.kaggle.com/sasanj/human-activity-smart-devices?select=smartphone.csv 

# prep function extracts/transfroms and loads data 
# giving a dataframe with activity in binary 

# corr_mat creates correaltion matrix for activity on each date 

# day_plots extacts like days fromt the data frame and plots the activity

def prep(df_pd): 

    # filter data by source type
    # drop unused columns 
    # split datetime and preserve original 

    df_activity = df_pd[df_pd['source'] == 'activity']

    df_activity = df_activity.drop(columns=['index', 'source'])

    df_activity['datetime'] = df_activity['timestamp']

    df_activity[['Date', 'Time']] = df_activity.timestamp.str.split(expand=True)

    df_activity = df_activity.reset_index(drop=True)

    # unpacy acitivity string and binarise acitivity values

    values = df_activity['values']

    values = pd.DataFrame((ast.literal_eval(i) for i in values), columns=['activity'])

    activity = pd.DataFrame((i.split(':')[0] for i in values['activity']), columns = ['most_active'])

    df_pd = pd.merge(df_activity, activity, left_index=True, right_index=True)

    df_most_active = df_pd.drop(columns=['values', 'timestamp'])

    df_most_active['active_state'] = (df_most_active['most_active'] != 'STILL').astype(int)

    df_active_state = df_most_active.drop(columns=['most_active'])

    # convert column to date time formate and set weekday names

    df_active_state['Date'] = pd.to_datetime(df_active_state['Date'])

    df_active_state['day'] = [calendar.day_name[i.weekday()] for i in df_active_state['Date']]

    df_active_state = df_active_state.sort_values(by=['Date', 'Time'])

    # df_active_state.to_csv('active_stat.csv')


    return df_active_state


def corr_mat(df_active_state):

    # filter out weekends
    df_active_state = df_active_state[df_active_state['day'] != 'Saturday']
    df_active_state = df_active_state[df_active_state['day'] != 'Sunday']

    # set datetime index for aggreagting in time
    df_active_state = df_active_state.set_index(pd.DatetimeIndex(pd.to_datetime(df_active_state.datetime)))
    dates = df_active_state.Date.unique()
    df_list = []

    # loop over each date 
    # extarct activity between certain time interval and agg 5mins
    # padding used to equalise activity data length

    for date in dates:

        temp = df_active_state[df_active_state['Date'] == date]
        temp = temp.between_time('10:00', '16:00')
        temp = temp.resample('300s').pad()
        temp = temp.active_state[1:].tolist()
        temp += [0]*(72-len(temp))
        
        df_list.append(temp)


    dates = [str(d)[:-19] for d in dates]
    d = dict(zip(dates, df_list))

    # create pivoted data frame of dates and acitivyt values
    cor_df = pd.DataFrame(data=d)

    # calc correlation between dates
    cor_df = cor_df.corr()

    sb.heatmap(cor_df,annot=True)
    plt.show()

    return cor_df

def day_plots(df_actives_state):
    # colour list for plotting
    colour = ['blue', 'black', 'red']

    # get list of days and set midnit to midnight scale
    days = df_active_state.day.unique()

    now = datetime.datetime.now()
    midnight = now.replace(hour=0, minute=0, second=0, microsecond=0)
    mid2 = midnight + datetime.timedelta(hours=23, minutes=59)

    for i, day in enumerate(days): 
        # subset by day then get dates of days 
        df_days = df_active_state[df_active_state['day'] == day]
        dates = df_days.Date.unique()

        fig, ax = plt.subplots(nrows=len(dates)+1, ncols=1, figsize=(15, 15))

        xlim_m=(midnight, mid2)
        plt.setp(ax, xlim=xlim_m)

        for j, date in enumerate(dates):
            
            # subset by date
            # set index to datetime for plotting and grouping

            df_day_date = df_days[df_days['Date'] == date]
            df_day_date = df_day_date.set_index(pd.DatetimeIndex(pd.to_datetime(df_day_date.Time)))

            df_day_date = df_day_date.groupby(pd.Grouper(freq='1Min')).aggregate(np.sum)

            # thresh hold acitivty in 1 mins and subset acitivty for plotting
            # can be cleaned up 

            df_day_date['active_thresh'] = [1]*len(df_day_date)
            df_day_date['active_type'] = [0]*len(df_day_date)

            # dont need to set by colour - left over from old plotting     
            df_day_date.loc[df_day_date['active_state'] > 0, 'active_type']='blue'
            df_day_date.loc[df_day_date['active_state'] == 0, 'active_type']='red'
            df_day_date_blue = df_day_date[df_day_date['active_type']=='blue']
            df_day_date_red = df_day_date[df_day_date['active_type']=='red']
            
            # moving avergaes for smooth line
            tmp = np.array(df_day_date['active_state'].values.tolist())
            df_day_date['active_state'] = np.where(tmp > 1,1,tmp).tolist() 

            df_day_date['mov_av_5'] = df_day_date.iloc[:,0].rolling(window=5).mean()
            df_day_date = df_day_date.fillna(value=0)

            ax[j].bar(df_day_date_blue.index, df_day_date_blue['active_thresh'], width = 0.0005, color = 'blue', label='Active')
            ax[j].bar(df_day_date_red.index, df_day_date_red['active_thresh'], width = 0.0005, color = 'red', label='Inactive')
            ax[-1].plot(df_day_date.index, df_day_date.mov_av_5+((j+1)*3), color=colour[j], label=str(date)[:-19])
            
            ax[j].legend()
            ax[-1].legend()

            ax[-1].set_xlabel('Time (Hours)')
            ax[-1].set_ylabel('realtive 5 min movav')
            ax[j].set_xlabel('Time (Hours)')
            ax[j].set_ylabel('Activity')

            ax[j].title.set_text(str(date)[:-19])

            ax[-1].xaxis_date()
            ax[-1].xaxis.set_major_formatter(mdates.DateFormatter('%H-%M-%S'))
            
            ax[j].xaxis_date()
            ax[j].xaxis.set_major_formatter(mdates.DateFormatter('%H-%M-%S'))
            plt.gcf().autofmt_xdate()

        plt.suptitle('Activity data -' + str(day))
        plt.savefig('activity' + str(day) + '.png')
        

def main(filename):

    df_pd = pd.read_csv(filename)

    df_active_state = prep(df_pd)

    corr_mat(df_active_state)   


