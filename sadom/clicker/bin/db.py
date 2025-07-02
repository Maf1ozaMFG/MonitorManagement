from psycopg2 import DatabaseError, connect
import pandas as pd
from bin.config_parse import get_item_from_config


def db_connect(params_dic):
    conn = None
    try:
        conn = connect(**params_dic)
    except (Exception, DatabaseError) as error:
        print(error)
        exit()
    return conn


def get_data_from_source(s):
    connection = db_connect(get_item_from_config('DB_CREDS'))
    try:
        return pd.read_sql(s, connection)
    except Exception as e:
        print('======> %s' % e)
        return pd.DataFrame()
    finally:
        connection.close()


def get_tasks_table():
    query = f'''
                SELECT *
                FROM tech_data.tech_screen_grabber_cfg
                WHERE active is TRUE
             '''
    return get_data_from_source(query).to_dict('records')


def get_clicker_cfg_table(preset=None):
    query = f'''
                SELECT *
                FROM tech_data.tech_cfg_clicker_screens
                
             '''
    if preset:
        query += f'''
            WHERE preset = '{preset}'
        '''
    return get_data_from_source(query).to_dict('records')


def get_grafana_cfg_table():
    query = f'''
                SELECT *
                FROM tech_data.tech_grafana_widgets
             '''
    return get_data_from_source(query).to_dict('records')


def get_clicker_filters():
    query = f'''
                select 
                    distinct incident_code 
                from tech_data.tech_screen_grabber_cfg
                where 
                    active is true
                    and temporarily_inactive is not true
                    and incident_code is not null
                order by incident_code 
             '''
    return get_data_from_source(query).to_dict('records')


def get_grafana_urls():
    query = f'''
                select 
                    min(widget_id) as widget_id
                    , short_name 
                    , case 
                        when starts_with(short_name, '!') then widget_url
                        else dashboard_url
                    end	as url
                from tech_data.tech_grafana_widgets
                where short_name is not null
                group by short_name, url
             '''
    return get_data_from_source(query).to_dict('records')


def get_presets():
    query = f'''
                SELECT DISTINCT preset 
                FROM tech_data.tech_cfg_clicker_screens
             '''
    return get_data_from_source(query).to_dict('records')


if __name__ == '__main__':
    pass
