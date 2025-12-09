import os
import pandas as pd
import PROJETO_PLANTAE.app.db as db
#from PROJETO_PLANTAE.app.utils.api_control import can_call_api
#from ..utils.api_control import can_call_api

conn  = db.get_db_connection()
cursor = conn.cursor()
cursor.execute("ALTER TABLE comentarios2 DROP FOREIGN KEY comentarios2_ibfk_1, DROP FOREIGN KEY comentarios2_ibfk_2")
conn.commit()
cursor.close()
conn.close()

