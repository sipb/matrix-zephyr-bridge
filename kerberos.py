import os
from constants import *

def renew_kerberos_tickets():
    """
    Get new working kerberos tickets
    """
    os.system(f"kinit {OWN_KERB}@{DEFAULT_REALM} -k -t daemon_matrix.keytab")
