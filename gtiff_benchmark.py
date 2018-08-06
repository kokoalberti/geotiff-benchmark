"""
gtiff_benchmark.py - Test utility for benchmarking geotiff compression
"""
import os
import argparse
import glob
import configparser
import sys
import subprocess
import tempfile

def parse_config(config_file='config.ini'):
    """
    Parse the configuration file into a more usable dictionary, with all the
    different options as keys, and a list of creation option arguments to pass 
    to gdal_translate as a value.
    """
    config_dict = {}
    
    config = configparser.ConfigParser()
    config.read(config_file)
    config.optionxform = str
    
    for section in config.sections():
        if section.lower() == 'default':
            continue
        
        options = []
        for item in config.items(section):
            options.extend(["-co", "{}={}".format(item[0].upper(), item[1])])
            
        config_dict.update({section: options})

    return config_dict
        
def perf(cmd=['sleep','1'], rep=1):
    """
    Use python's subprocess module to run a command with 'perf stat' and 
    return the 'task-clock' part of the perf stat output.
    """
    command = ['perf', 'stat', '-x', '^','-r', str(rep)]
    command.extend(cmd)

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
    parser.add_argument('--config', help='Config file to use', 
                        default='config.ini')
    parser.add_argument('--repetitions', help='Number of reps', default=1)
    parser.add_argument('--input', help='Directory with input files',
                        default=os.path.join(base_dir,'input_rasters'))
    args = parser.parse_args()
    
    # Test that perf stat is working
    print("Testing that stat perf works...")
    try:
        task_clock = perf()
        print("Looks good!")
    except Exception as e:
        print("Something went wrong testing out a stat perf command! Without "
              "perf stat this is not going to work...")
        sys.exit(1)
    
    # Parse configuration file and input files
    config = parse_config(config_file=args.config)
    
    # Let's run some tests!
    results = ['test;file;option;time;size']
    for path in glob.glob(os.path.join(args.input, "*.tif")):
        
        filename = os.path.basename(path)
        
        # Create a temporary directory for all the tests with this file
        with tempfile.TemporaryDirectory(prefix='gtiff-benchmark-') as tmpdir:
            
            # Create the base version of the input file.
            base_file = os.path.join(tmpdir, 'base.tif')
            cmd = ['gdal_translate', '-q', path, base_file, '-co', 'TILED=YES', 
                   '-co', 'COMPRESS=NONE', '-co', 'COPY_SRC_OVERVIEWS=NO']
            subprocess.run(cmd)
            
            # Run the tests...
            for option in config.keys():
                # Run the write tests on the base_file, saving the result to
                # the option_file
                print("WRITE test: Running with option '{}' on file '{}'".format(option, filename))
                
                option_file = os.path.join(tmpdir, option+'.tif')
                cmd = ['gdal_translate', '-q', base_file, option_file, *config.get(option)]

                try:
                    task_clock = perf(cmd=cmd, rep=args.repetitions)
                    file_size = os.stat(option_file).st_size / (1024.0*1024.0)
                    print("WRITE test: Completed {} repetitions. Average time: {:.2f}s File size: {:.1f}Mb".format(args.repetitions, task_clock, file_size))
                except Exception as e:
                    try: os.remove(option_file)
                    except: pass
                    print("WRITE test: Failed!")
                    task_clock = ''
                    file_size = ''
                finally:
                    results.append('{};{};{};{};{}'.format('write', filename, option, task_clock, file_size))
                    
                # Run the read tests on the just created file by decompressing
                # it again.
                print("READ test: Running on file '{}'".format(option+'.tif'))
                read_file_output = os.path.join(tmpdir, 'read.tif')
                cmd = ['gdal_translate', '-q', option_file, read_file_output, 
                       '-co', 'TILED=YES', '-co', 'COMPRESS=NONE']
                       
                try:
                    task_clock = perf(cmd=cmd, rep=args.repetitions)
                    print("READ test: Completed {} repetitions. Average time: {:.2f}s".format(args.repetitions, task_clock))
                except Exception as e:
                    print("READ test: Failed!")
                    task_clock = ''
                finally:
                    results.append('{};{};{};{};{}'.format('read', filename, option, task_clock, ''))
                    
    # Write the results to the results file and to stdout
    result_csv = '\n'.join(results)
    with open('results.csv', 'w') as f:
        f.write(result_csv)
    print("===========================================================")
    print("Benchmark complete! Results:")
    print("-----------------------------------------------------------")
    print(result_csv)
    print("===========================================================")