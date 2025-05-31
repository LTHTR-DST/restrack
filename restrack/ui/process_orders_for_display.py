import pandas as pd
import panel as pn
from bokeh.models.widgets import HTMLTemplateFormatter
from bokeh.models.widgets.tables import DateFormatter


def process_orders_for_display(df: pd.DataFrame) -> pn.widgets.Tabulator:
    df_to_view = df.loc[
        :,
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
        ],
    ]

    # Replace NaN values with "-"
    df_to_view = df_to_view.fillna("-")

    df_to_view.rename(
        columns={
            "patient_id": "Patient ID",
            "proc_name": "Investigation",
            "current_status": "Status",
            "order_datetime": "Ordered",
            "in_progress": "In progress",
            "partial": "Partial",
            "complete": "Complete",
            "supplemental": "Supplemental",
            "status": "User Status",
            "user_note": "User Note",
        },
        inplace=True,
    )

    _ = {
        1: "waiting for review",
        10: "no show",
        11: "supplemental",
        2: "data not collected",
        3: "scheduled",
        4: "in progress",
        5: "partial",
        6: "complete",
        7: "cancelled",
        8: "resolved",
        9: "entered",
        -1: "NA ",
    }
    # df_to_view["Status"] = df_to_view["Status"].astype(int).map(status_desc)
    status_format_template = """
    <b><div style="background:
        <%= (function colorfromint(){
            if(Status == 6){
                return("#00FF0055")
            }
            else if(Status == 5){
                return("#FFFF0055")
            }
            else if([3,9].includes(Status)){
                return ("#0000FF55")
            }
            else if(Status == 11){
                return ("#FF000055")
            }
            else if(Status  == 1 || Status == -1){
            return("White")
            }
            else {return ("#00000055")}
         }()) %>;"> <%= Status %> </div></b>
    """

    status_formatter = HTMLTemplateFormatter(template=status_format_template)
    date_formatter = DateFormatter(format="%d/%m/%Y")

    formatters = {
        "Status": status_formatter,
        "Ordered": date_formatter,
        "In progress": date_formatter,
        "Partial": date_formatter,
        "Complete": date_formatter,
        "Supplemental": date_formatter,
    }

    tbl = pn.widgets.Tabulator(
        df_to_view,
        layout="fit_data_stretch",
        groupby=["Patient ID"],
        hidden_columns=["index", "order_id", "Patient ID"],
        pagination="local",
        page_size=None,
        selectable="checkbox-single",
        disabled=True,
        formatters=formatters,
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
