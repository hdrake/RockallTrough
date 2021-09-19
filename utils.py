import xmitgcm as xmit
import xarray as xr

def load_all_data():
    return xr.open_zarr("data/interim/c_Zint")
    
    