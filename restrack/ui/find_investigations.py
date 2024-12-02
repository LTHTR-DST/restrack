import panel as pn
from restrack.data_access.find_orders import orders_for_patient
from restrack.data_access.find_ttables_for_user import find_ttables
from functools import partial
import pandas as pd
from bokeh.io import curdoc


#from data_access import store_tags

class Find_investigations():

    def __init__(self,user):  
        curdoc().clear()
        self.user='user1'
        pn.extension('tabulator',sizing_mode="stretch_width")
        self.results_tabulator_object = pn.widgets.Tabulator()
        self.taglist=pd.DataFrame()#initalise variable for update taglist-part of failed attempt to put an event listener on the table
        self.output=self.display_handler()
     

    def clickhandler(self,clicked):
        if clicked:
            return self.binding1
      
    
    def selection_saver(self):
        print("function has run" )
        selection = self.results_tabulator_object.selected_dataframe
        print(selection)
    
    def clickhandler2(self, clicked):
            if (clicked):
                self.selection_saver()
            

    def show_table(self,hn):
        self.results_tabulator_object = pn.widgets.Tabulator(orders_for_patient(hn),selectable='checkbox', selection=[], hidden_columns=['index','order_id'])
        return self.results_tabulator_object
    
    def show_tracking_tables(self):
        #self.user isn't recognised as an arg so substituted sting literal meanwhile
        ttables_for_user = pn.widgets.Tabulator(find_ttables(self.user),selectable='checkbox', selection=[])
        return ttables_for_user

    def display_handler(self): 
        hosp_numb = pn.widgets.TextInput(name='Hospital number', width = 200)
        enter_hosp_no = pn.widgets.Button(name="Enter",button_type='primary', width=100)
        select_button=pn.widgets.Button(name="Tag Selected Investigations", button_type='primary',width=500)
        table_select_button=pn.widgets.Button(name="Select table to track on", button_type='primary',width=500)
        hn=hosp_numb.param.value
        self.binding1=pn.bind(self.show_table, hn) 
        self.show_table=pn.bind(self.clickhandler,enter_hosp_no)
        pn.panel(pn.bind(self.clickhandler2, select_button))#mysteriously doesn't work if this binding is not panel!



        output=pn.template.GoldenTemplate(
        title="Select Investigations To Tag",
        main=[
        pn.Column(
        pn.Row(hosp_numb, enter_hosp_no),
        pn.Row(pn.panel(self.show_table)),
        pn.Row(select_button),
        pn.Row("Select the tables you want to track on"),
        #pn.Row(display_tracking_tables),
        pn.Row(table_select_button))]
        ).servable()    

        return output

        #pn.serve(output,port=5000)
