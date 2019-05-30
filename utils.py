# %%writefile easyinfo/utils.py
"""
Easy debug printing, timing, and variable attributes (length, width) for Python.

"""
# if (sys.version_info < (3, 0)):
from __future__ import print_function
import sys
import inspect
import time
# from IPython.core.display import display, HTML
import pickle
import os
import regex as re
import csv

# Confounding variable names that we don't want from the stack.
# Not a comprehensive or generalized list
default_var_names = {'var', 'kwargs', 'script_name', 'mod_spec', 'interactivity', 'fd_obj', '_i10', '_i5', '_ih', 'loader', 'ncallbacks', '_exit_code', 'fd', 'parent', 'vname', 'metadata', 'pkg_name', '_i16', '_ii', '_i1', '__builtins__', 'msg_id', 'handler_func', 'cached'}

# Return the frame num_back frames ago.
def prev_frame(num_back=1):
  curr_frame = inspect.currentframe()
  for _ in range(num_back):
    curr_frame = curr_frame.f_back
  return curr_frame

# Print name of variable with value
# arg_i is the index of the argument in the function being called num_back frames ago
#  if arg_i is -1, the name receiving variable of the receiving variable is returned
#  e.g. var_name = vname(arg_i=-1) => returns 'var_name'
def vname(var=None, num_back=2, func_name='vname', arg_i=0, arg_name=None):
  code = inspect.getframeinfo(prev_frame(num_back))[3][0]
  var_name = ''
  if arg_i < 0:
    receiving_pattern = r'(\p{L}\w+)\s*=\s*'+func_name+r'\s*\('
    var_search = re.search(receiving_pattern, code)
    if var_search:
      var_name = var_search.group(1)
  else:
    args_start = code.find(func_name+'(') + len(func_name) + 1 # +1 for (
    args_end = len(code) - code[::-1].find(')') - 1 # Search from the end, in case there's another function call inside
    args_str = code[args_start:args_end]
    if arg_name:
      named_pattern = func_name+r'\s*=\s*(\p{L}\w+)'
      var_search = re.search(named_pattern, args_str)
      if var_search:
        var_name = var_search.group(1)
    else:
      var_name = args_str.split(",")[arg_i].strip()
  if not var_name:
    var_name = ''
  else:
    var_name = var_name.replace("self.", "") # For loading class variables
  return var_name

def vline(num_back=2): # Credit to http://code.activestate.com/recipes/145297-grabbing-the-current-line-number-easily/
    """Returns the current line number in our program."""
    return prev_frame(num_back).f_lineno
      
# Print to standard error.
# Similar to vprint by default, or just print a given msg
def eprint(var, msg=None, verbose=None, **kwargs):
  if msg is None:
    msg = vstr(var, func_name='eprint', num_back=4, verbose=verbose)
  print(msg, file=sys.stderr)

def vstr(var, name=None, val=None, func_name='vstr', num_back=3, verbose=None):
  if not val:
    val = var
  msg = None
  if not name:
    name = vname(var, num_back, func_name)
  msg = name
  if verbose is not False:
    msg += " (line " + str(vline(num_back)) + ") <" + var.__class__.__name__+">"
  msg += ": " + str(val)
  return msg
  
# Print a variable, with its name and value
# If verbose is not False, will print line number of function call
#   and type of variable
# Specify name to print a message instead of the variable name
def vprint(var, name=None, val=None, verbose=None, **kwargs):
  msg = vstr(var, name, val, func_name='vprint', num_back=4, verbose=verbose)
  print(msg, **kwargs)
  
# Similar to vprint, but prints __repr__ instead of __str__
def rprint(var, name=None, val=None, verbose=None, **kwargs):
  if not val:
    val = var
  msg = vstr(var, name, val=repr(val), func_name='rprint', num_back=4, verbose=verbose)
  print(msg, **kwargs)

# Similar to vprint, but prints dir(var) instead of str(var)
def dprint(var, name=None, val=None, verbose=None, **kwargs):
  if not val:
    val = var
  msg = vstr(var, name, val=dir(val), func_name='dprint', num_back=4, verbose=verbose)
  print(msg, **kwargs)

def lstr(var, name=None, val=None, max_depth=10, func_name='lstr', num_back=3, verbose=None):
  attr_name = 'len'
  if not val:
    if hasattr(var, '__len__') and not hasattr(var, 'shape'):
      val = str(len(var))
      if not isinstance(var, dict) and len(var) > 0 and hasattr(var, '__getitem__') and not isinstance(var[0], str):
        inner_var = var[0]
        depth = 0
        var_len = vlen(inner_var)
        attr_name = 'shape'
        while var_len > 1 and not isinstance(inner_var, str):
          if hasattr(inner_var, 'shape'):
            for axis in inner_var.shape:
              val += " x "+str(axis)
            break
          val += " x "+str(vlen(inner_var))
          if depth >= max_depth:
            break
          try:
            inner_var = inner_var[0]
          except TypeError:
            if vwid(inner_var):
              val += " x "+str(vwid(inner_var))
            break
          var_len = vlen(inner_var)
    elif hasattr(var, 'shape'):
      val = var.shape
      attr_name = 'shape'
    elif hasattr(var, 'size'):
      val = var.size
      attr_name = 'size'
    else:
      attr_name = 'value'
      val = var
  if not name:
    name = vname(var, num_back, func_name)
  msg = name
  if verbose is not False:
    msg += " (line " + str(vline(num_back)) + ") " + str(type(var)) + " " + attr_name
  msg += ": " + str(val)
  return msg
  
# Print len
def lprint(var, name=None, val=None, num_back=4, verbose=None, **kwargs):
  msg = lstr(var, name, val, func_name='lprint', num_back=4, verbose=verbose)
  print(msg, **kwargs)

# Get str of all printing functions output
def astr(var, name=None, val=None, func_name='astr', num_back=4, verbose=None):
  msg = lstr(var, name, val, func_name=func_name, num_back=num_back, verbose=verbose) + "\n" + \
    vstr(var, "\t", val, func_name=func_name, num_back=num_back, verbose=verbose)
  return msg

# Call all printing functions for variable
def aprint(var, name=None, val=None, verbose=None, **kwargs):
  msg = astr(var, name, val, func_name='aprint', num_back=5, verbose=verbose)
  print(msg, **kwargs)

def vlen(var):
  try:
    if var is None:
      return 0
    elif hasattr(var, 'shape'):
      val = var.shape
    elif hasattr(var, '__len__'):
      val = len(var)
    elif hasattr(var, 'size'):
      val = var.size
    else:
      return 0
    if hasattr(val, '__len__'):
      if len(val):
        val = val[0]
      else:
        return 0
  except TypeError: # e.g. set that doesn't support indexing
    return 0
  return val

def vwid(var):
  try:
    if var is None:
      return 0
    elif hasattr(var, 'shape'):
      val = var.shape
      if len(val) > 1:
        val = val[1]
      else:
        val = 1
    elif hasattr(var, '__len__'):
      if len(var) > 0:
        val = vlen(var[0])
      else:
        val = 0
    elif hasattr(var, 'size'):
      val = var.size
    else:
      return 0
  except TypeError: # e.g. set that doesn't support indexing
    return 0
  return val

# Turn 'path/filename.txt' into 'path/filename_suf.txt'
def add_file_suffix(filename, suf):
  name, ext = os.path.splitext(filename)
  return name+"_"+str(suf)+ext

# Turn 'path/filename.txt' into 'path/pref_filename.txt'
def add_file_prefix(filename, pre):
  dirname = os.path.dirname(filename)
  basename = os.path.basename(filename)
  return os.path.join(dirname, str(pre)+"_"+basename)

# Use pickle to save an object
# If filepath include a filename at end, use that filename
# If filepath is a directory, save object as filepath/variable_name.pkl
  # Also, save directory as a global variable _save_dir so that it's only needed once
# If no filepath is given, save object as variable_name.pkl in current dir
# If filepath ends in .txt, save as plain text.
# If filepath ends in .csv, save as csv.
# If filepath is just an extension: '.pkl', '.txt' or '.csv', save as that type of file
#   using the variable name as file basename
global _save_dir
_save_dir = ''
def vsave(obj, filepath=None, sort=True, save_dir=None, verbose=True,):
  global _save_dir
  if save_dir:
    if filepath:
      filepath = os.path.join(save_dir, filepath)
    _save_dir = save_dir
  var_name = vname(obj, num_back=3, func_name='vsave')
  ext = None
  if filepath:
    filename, ext = os.path.splitext(filepath)
    if filename.startswith('.'): # If only extension was provided
      ext = filename
      filename = var_name
    if not ext: # If no extension, assume directory
      _save_dir = filename # Save directory for future calls
    elif ext == '.txt':
      filepath = filename + ext
      with open(filepath, 'w') as txt_file:
        if isinstance(obj, list):
          for item in obj:
            txt_file.write(str(item)+"\n")
        elif isinstance(obj, dict):
          items = obj.items()
          if sort:
            items = sorted(items, key=lambda kv: kv[1], reverse=True)
            
          for key, val in items:
            txt_file.write(str(key)+": "+str(val)+"\n")
        else:
          txt_file.write(str(obj)+"\n")
        if verbose:
          print("To load saved variable: "+var_name+" = vload('"+filepath+"')")
        return
    elif ext == '.csv' or ext == '.tsv':
      filepath = filename + ext
      with open(filepath, 'w') as csv_file:
        if ext == '.csv':
          delimiter = ','
        else:
          delimiter = '\t'
        writer = csv.writer(csv_file, delimiter=delimiter)
        for row in obj:
          writer.writerow(row)
      if verbose:
        print("To load saved variable: "+var_name+" = vload('"+filepath+"')")
      return
        
  else:
    filepath = _save_dir
  
  if not ext: # Is a filename specified with extension?
    # If not, use argument name and .pkl
    filename = var_name + '.pkl'
    filepath = os.path.join(_save_dir, filename) # Use specified or saved directory
  with open(filepath, 'wb') as bin_file:
    pickle.dump(obj, bin_file)
  if verbose:
    print("To load saved variable: "+var_name+" = vload('"+filepath+"')")

# Load pickled object from filename
# If argument is not a string, use name of argument to assume filename
# If no arguments are given or filepath is a string but with no extension,
#   use receiving variable name as filename (e.g. 'test_var.pkl' for test_var = vload())
# Also, for a filepath with no extension, use it as the directory
# load_dir can be specified if different than _save_dir
def vload(filepath=float('inf'), load_dir=None, verbose=True):
  ext = ''
  if not load_dir:
    global _save_dir
    load_dir = _save_dir
  if not isinstance(filepath, str): # If None or an object
    if filepath == float('inf'): # No filepath argument provided
      # Use name of receiving variable
      filepath = vname(filepath, num_back=3, func_name='vload', arg_i=-1)
    else:
      filepath = vname(filepath, num_back=3, func_name='vload')
    filepath += ".pkl"
  else:
    filename, ext = os.path.splitext(filepath)
    if filename.startswith('.'): # If only extension was provided
      ext = filename
      var_name = vname(filepath, num_back=3, func_name='vload', arg_i=-1)
      filepath = var_name + ext
    elif not ext: # Is filepath a directory?
      load_dir = filename
      filepath = vname(filepath, num_back=3, func_name='vload', arg_i=-1)
      filepath += ".pkl"
  if load_dir:
    filepath = os.path.join(load_dir, filepath)
  if ext == '.txt':
    with open(filepath, 'r', newline='') as txt_file:
      loaded_var = []
      for line in txt_file:
        loaded_var.append(line.strip())
  elif ext == '.csv' or ext == '.tsv':
    with open(filepath, 'r', newline='') as csv_file:
      if ext == '.csv':
        delimiter = ','
      else:
        delimiter = '\t'
      reader = csv.reader(csv_file, delimiter=delimiter)
      loaded_var = []
      for row in reader:
        loaded_var.append(row)
  else:
    with open(filepath, 'rb') as bin_file:
      loaded_var = pickle.load(bin_file)
  if verbose:
    filepath_str = filepath
    if len(filepath_str) > 50:
      filepath_str = '.../'
      # TODO: Include the last directory also
      filepath_str += os.path.basename(filepath)
    lprint(loaded_var, "Loaded variable from "+filepath_str)
  return loaded_var

_start_time = time.time()
_start_stack = [_start_time]
_last_time = None
_start_ids = {} # key: id, value: (start_time, last_time)

# id: Dictionary key, to track which start time and last time to use with end()
def start(id=None):
  """Gets and prints the spreadsheet's header columns

  Parameters
  ----------
  file_loc : str
      The file location of the spreadsheet
  print_cols : bool, optional
      A flag used to print the columns to the console (default is False)

  Returns
  -------
  list
      a list of strings representing the header columns
  """
  global _start_time, _last_time
  _last_time = None
  _start_time = time.time()

# msg: message to print before time. If only id is provided, 
# use id for msg. If neither is provided, use "Total time"
# id: 
def end(msg=None, verbose=True):
  end_time = time.time()
  global _start_time, _last_time
  total_time = end_time - _start_time
  if verbose:
    if not msg:
      msg = 'Total time'
    if _last_time:
      since_time = end_time - _last_time
      msg += ': '+str(total_time)+' Time since last: '+str(since_time)
      print(msg)
    else:
      vprint(total_time, name=msg)
  else:
    since_time = end_time - _last_time
  _last_time = time.time()
  return since_time

# Return an int, removing any non-digit chars other than . or -
def to_int(text):
  if isinstance(text, int):
    return text
  try:
    text = int(text)
    return text
  except ValueError:
    text = str(text)
    text_digits = ""
    for c in text:
      if c.isdigit() or c == '.' or c == '-':
        text_digits += c
    if text_digits:
      try:
        return int(text_digits)
      except ValueError:
        return False
    else:
      return False

# Return int if possible or float otherwise.
def to_num(text):
  if isinstance(text, int):
    return text
  try:
    text_float = float(text)
    text_int = int(text)
    if text_int == text_float:
      return text_int
    return text_float
  except ValueError:
    text = str(text)
    text_digits = ""
    for c in text:
      if c.isdigit() or c == '.' or c == '-':
        text_digits += c
    if text_digits:
      try:
        return int(text_digits)
      except ValueError:
        try:
          score = float(score)
        except ValueError:
          pass
        return False
    else:
      return False
