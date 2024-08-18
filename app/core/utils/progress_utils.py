from tqdm import tqdm


def get_tqdm(total, desc, leave=True, dynamic_ncols=True):
    return tqdm(total=total, desc=desc, leave=leave, dynamic_ncols=dynamic_ncols)
