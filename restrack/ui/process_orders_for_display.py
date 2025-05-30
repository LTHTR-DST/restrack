import pandas as pd
import panel as pn
from bokeh.models.widgets import HTMLTemplateFormatter


def process_orders_for_display(df):
    df_to_view = df[
        [
            "order_id",
            "patient_id",
            "proc_name",
            "current_status",
            "order_datetime",
            "in_progress",
            "partial",
            "complete",
            "supplemental",
            "status",
            "user_note",
        ]
    ]

    df_to_view["order_datetime"] = pd.to_datetime(
        df_to_view["order_datetime"], format="mixed"
    )
    df_to_view["order_datetime"] = df_to_view["order_datetime"].dt.strftime("%d/%m/%Y")
    df_to_view["in_progress"] = pd.to_datetime(
        df_to_view["in_progress"], format="mixed"
    )
    df_to_view["in_progress"] = df_to_view["in_progress"].dt.strftime("%d/%m/%Y")
    df_to_view["partial"] = pd.to_datetime(df_to_view["partial"], format="mixed")
    df_to_view["partial"] = df_to_view["partial"].dt.strftime("%d/%m/%Y")
    df_to_view["complete"] = pd.to_datetime(df_to_view["complete"], format="mixed")
    df_to_view["complete"] = df_to_view["complete"].dt.strftime("%d/%m/%Y")
    df_to_view["supplemental"] = pd.to_datetime(
        df_to_view["supplemental"], format="mixed"
    )
    df_to_view["supplemental"] = df_to_view["supplemental"].dt.strftime("%d/%m/%Y")

    # Replace NaN values with "-"
    df_to_view = df_to_view.fillna("-")

    df_to_view.rename(
        columns={
            "proc_name": "Investigation",
            "current_status": "Status",
            "order_datetime": "Ordered",
            "in_progress": "In progress",
            "status": "User Status",
            "user_note": "User Note",
        },
        inplace=True,
    )

    """ 1	waiting for review
    10	no show
    11	supplemental
    2	data not collected
    3	scheduled
    4	in progress
    5	partial
    6	complete
    7	cancelled
    8	resolved
    9	entered
    -1	NA """

    status_format_template = """
    <b><div style="background:
        <%= (function colorfromint(){
            if(Status == 6){
                return("Green")
            }
            else if(Status == 5){
                return("Yellow")
            }
            else if([3,9].includes(Status)){
                return ("Blue")
            }
            else if(Status == 11){
                return ("Red")
            }
            else if(Status  == 1 || Status == -1){
            return("White")
            }
            else {return ("Black")}
         }()) %>;"> <%= Status %> </div></b>
    """

    status_formatter = HTMLTemplateFormatter(template=status_format_template)

    tbl = pn.widgets.Tabulator(
        df_to_view,
        layout="fit_data_stretch",
        groupby=["patient_id"],
        hidden_columns=["index", "order_id", "patient_id"],
        pagination="local",
        page_size=None,
        selectable="checkbox",
        disabled=True,
        formatters={"Status": status_formatter},
        sizing_mode="scale_both",
    )

    return tbl

    # def colour_rows(row):
    #     if row["complete"] != "nan":
    #         return ['background-color: green'] * len(row)
    #     else:
    #         return [''] * len(row)

    # styled = tbl.style.map(colour_rows, axis=1)

    # return styled
