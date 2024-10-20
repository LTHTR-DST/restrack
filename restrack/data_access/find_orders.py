import os
from datetime import datetime
from time import strftime
from dateutil import parser
from typing import Optional
import pandas as pd
from restrack.models import cdm
from dotenv import find_dotenv, load_dotenv
from sqlmodel import Field, Session, SQLModel, create_engine, func, select

load_dotenv(find_dotenv())

DATABASE_CONNECTION_STRING = os.getenv("DATABASE_CONNECTION_STRING")


engine = create_engine(DATABASE_CONNECTION_STRING)

def orders_for_patient(patient_id):
    if patient_id !="":
        patient_id = int(patient_id)
        with Session(engine) as session:
            statement = select(cdm.ORDER.order_datetime, cdm.ORDER.proc_name, cdm.ORDER.order_id,cdm.PROVIDER.provider_name).outerjoin_from(cdm.ORDER,cdm.PROVIDER,cdm.ORDER.order_requested_by == cdm.PROVIDER.provider_id).where(cdm.ORDER.patient_id==patient_id) 
            orders_df= pd.read_sql(statement,session.bind)
    orders_df.sort_values(by='order_datetime', ascending=False, inplace=True) 
    orders_df['order_datetime'] = pd.to_datetime(orders_df['order_datetime'], format='mixed')
    orders_df['order_datetime'] = orders_df['order_datetime'].dt.strftime('%d/%m/%Y')
    orders_df.rename(columns={'order_datetime':'Date','proc_name':'Investigation'}, inplace=True)
    print(orders_df)
 
   
    return orders_df
    


orders_for_patient(2752126)