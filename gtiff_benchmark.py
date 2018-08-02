"""
gtiff_benchmark.py - Test utility for benchmarking geotiff compression

To do:
- configurable results file via --results arg
- use temporary directory via --dir arg
"""
import os
import argparse
import glob
import configparser
import sys
import random
import subprocess

from osgeo import gdal
from collections import OrderedDict

def parse_files():
    """
    Create an ordered dict from the .tif files in the input dir
    """
    files = OrderedDict()

    for path in glob.glob(os.path.join(args.input, "*.tif")):
        filename = os.path.basename(path)
        files.update({filename:path})

    return files

def parse_config(config_file='config.ini'):
    """
    Parse the configuration file
    """
    config = configparser.ConfigParser()
    config.read(config_file)
    config.optionxform = str
    return config

def prepare():
    """
    Prepare a testing environment by creating a base version of each input
    raster without compression, tiling, etc.
    """
    files = parse_files()

    # Process the input_rasters to test_rasters
    for name, path in files.items():
        try:
            ds_src = gdal.Open(path)
            
            target_dir = os.path.join(base_dir, 'test_rasters', name, 'base')
            target_file = os.path.join(target_dir, 'base.tif')
            
            options = ['TILED=NO', 'COMPRESS=NONE', 'COPY_SRC_OVERVIEWS=NO']
            
            os.makedirs(target_dir)
        
            ds_dst = drv.CreateCopy(target_file, ds_src, options=options)
            ds_dst = None
            print("Prepared base version of '{}'".format(name))
        except Exception as e:
            print("Failed while preparing '{}'. Skipping.".format(name))


def test_read():
    """
    Read and decompress a whole image.
    
    Tests decompression speed of the compression algorithm when by opening 
    the image with GDAL.
    """
    target_dir = os.path.join(base_dir, 'test_rasters', args.file, args.option)
    target_file = os.path.join(target_dir, args.option+'.tif')
    
    print("Reading file: {}".format(target_file))
    ds = gdal.Open(target_file)
    if ds is None:
        print("Could not open file '{}'".format(target_file))
        sys.exit(1)
    
    for bn in range(ds.RasterCount):
        bn += 1
        band = ds.GetRasterBand(bn)
        array = band.ReadAsArray(0, 0, band.XSize, band.YSize)
        band = None
    ds = None
    print("Completed.")    

def test_write():
    """
    Write an image file from an uncompressed base file. 
    
    Tests write speed and compression ratio.
    """
    
    gdal.UseExceptions()
    
    input_file = os.path.join(base_dir, 'test_rasters', args.file, 'base', 'base.tif')
    target_dir = os.path.join(base_dir, 'test_rasters', args.file, args.option)
    output_file = os.path.join(target_dir, args.option+'.tif')

    try: os.makedirs(target_dir)
    except: pass

    ds_src = gdal.Open(input_file)
    if ds_src is None:
        print("Could not open input file: {}".format(input_file))
        sys.exit(1)
        
    try:
        options = ["{}={}".format(o[0].upper(), o[1]) for o in config.items(section=args.option)]
        ds_dst = drv.CreateCopy(output_file, ds_src, strict=1, options=options)
        ds_dst = None
        print("Created '{}' version of '{}' at '{}'".format(args.option, args.file, output_file))
    except Exception as e:
        print("Exception while running job! {}".format(e))
        sys.exit(1)


def run():
    """
    Run the benchmark
    """
    files = parse_files()
    print("Loading config file '{}'".format(args.config))
    config = parse_config(config_file=args.config)

    
    print("Testing that stat perf works...")
    try:
        task_clock = perf()
        print("Looks good!")
    except Exception as e:
        print("Something went wrong testing out a stat perf command! Without "
              "perf stat this is not going to work...")
        sys.exit(1)
    
    #TODO: Use itertools.product to loop through everything in one loop, file/section/tests
    #TODO: Remove duplicate code of running read/write benchmarks
    results = ['test;file;option;time;size']
    for name, path in files.items():
        for section in config.sections():
            if section.lower() == 'default':
                continue
            
            # Run the write benchmark
            cmd = "/usr/bin/python3 {} benchmark --file {} --test {} --option {} --config {}".format(os.path.abspath(__file__), name, 'write', section, args.config)
            try:
                print("Running benchmark ({}x): {}".format(args.repetitions, cmd))
                task_clock = perf(cmd=cmd, rep=args.repetitions)
                
                # Check file size
                created_file = os.path.join(base_dir, 'test_rasters', name, section, section+'.tif')
                file_size = os.stat(created_file).st_size / (1024.0*1024.0)
                print("Completed {} repetitions. Average time: {:.2f}s File size: {:.1f}Mb".format(args.repetitions, task_clock, file_size))
            except Exception as e:
                print("Failed to run benchmark: {}".format(e))
                task_clock = ''
                file_size = ''
            
            # Append the result to the results list
            results.append('{};{};{};{};{}'.format('write', name, section, task_clock, file_size))

            #Run the read benchmark
            cmd = "/usr/bin/python3 {} benchmark --file {} --test {} --option {} --config {}".format(os.path.abspath(__file__), name, 'read', section, args.config)
            try:
                print("Running benchmark ({}x): {}".format(args.repetitions, cmd))
                task_clock = perf(cmd=cmd, rep=args.repetitions)
                print("Completed {} repetitions. Average time: {:.2f}s".format(args.repetitions, task_clock))
            except Exception as e:
                print("Failed to run benchmark: {}".format(e))
                task_clock = ''

            # Append the result to the results list
            results.append('{};{};{};{};{}'.format('read', name, section, task_clock, ''))

            
    # Write the results to the results file and to stdout
    result_csv = '\n'.join(results)
    with open('results.csv', 'w') as f:
        f.write(result_csv)
    print("===========================================================")
    print("Benchmark complete! Results:")
    print("-----------------------------------------------------------")
    print(result_csv)
    print("===========================================================")
        
def perf(cmd='sleep 1', rep=1):
    """
    Use python's subprocess module to run a command with 'perf stat' and 
    return the 'task-clock' part of the perf stat output.
    
    The 'perf stat' output is written to stderr. However, GDAL errors are 
    also written to stderr (for example when using a predictor of 2 on a 
    dataset which is not floating points). 
    
    We can't really tell if the perf command failed somehow as this can 
    can happen due to unforeseen circumstances in GDAL (i.e. using 
    PREDICTOR=2 on data not of Float32 type...) and then the command still
    returns a returncode of 0. So instead, we raise an exception when the 
    return code is not 0, or if parsing the output to something sensible
    fails.
    """
    command = ['perf', 'stat', '-x', '^','-r', str(rep)]
    command.extend(cmd.split(" "))
    result = subprocess.run(command, stdout=subprocess.PIPE, 
                            stderr=subprocess.PIPE)
    
    if result.returncode != 0:
        raise Exception("Running benchmark failed as perf returned a "
                        "non-zero return code. Here are some hints "
                        "from perf's stderr: {}".format(result.stderr))
               
    try:
        return float(result.stderr.split(b'^')[0].decode("utf-8"))/1000
    except:
        raise Exception("Running benchmark failed for "
                        "some reason. Here are some hints "
                        "from perf's stderr: {}".format(result.stderr))

if __name__ == '__main__':
    
    base_dir = os.path.split(os.path.abspath(__file__))[0]

    # Parse command line arguments
    parser = argparse.ArgumentParser(description="GTiff Benchmark")
    parser.add_argument('action', action='store', 
                        choices=['prepare', 'run', 'benchmark'], 
                        help='Action to perform.')
    parser.add_argument('--file', help='File to operate on')
    parser.add_argument('--test', help='What test to run')
    parser.add_argument('--option', help='Option/settings to run with')
    parser.add_argument('--config', help='Config file to use', 
                        default='config.ini')
    parser.add_argument('--repetitions', help='Number of reps', default=10)
    parser.add_argument('--input', help='Directory with input files',
                        default=os.path.join(base_dir,'input_rasters'))

    args = parser.parse_args()
    
    # Setup and config
    drv = gdal.GetDriverByName('GTiff')
    
    config = parse_config(config_file=args.config)
    
    if args.action == 'benchmark':
        # Run an individual benchmark
        print("Running '{}' test on file '{}' "
              "with option '{}'".format(args.test, args.file, args.option))
        
        if args.option not in config.sections():
            print("Config option '{}' not found in config "
                  "file '{}. Exiting.".format(args.option,args.config))
            sys.exit(1)
        
        if args.test == 'write':
            test_write()
            
        elif args.test == 'read':
            test_read()
            
        else:
            print("Not a valid test: {}".format(args.test))
            sys.exit(1)
               
    elif args.action == 'run':
        # Run all the benchmarks
        run()
        
    elif args.action == 'prepare':
        # Prepare uncompressed versions of the input files.
        prepare()

    