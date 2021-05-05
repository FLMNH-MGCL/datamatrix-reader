
mod lib;
extern crate image;
use std::time::Instant; 
extern crate clap;	
use clap::{Arg, App};

/// Program usage: run with --help flag to see usage
pub fn main() {
    let matches = App::new("Datamatrix Scanner")
    .version("1.0")
    .author("Aaron Leopold <aaronleopold1221@gmail.com>")
    .about("Decodes datamatrices and code128 barcodes from specimen images")
    .arg(Arg::with_name("start_dir")
        .short("d")
        .long("start_dir")
        .value_name("DIR")
        .help("Sets the starting path")
        .required(true)
        .takes_value(true))
    .arg(Arg::with_name("scan_time")
        .short("s")
        .long("scan_time")
        .value_name("TIME (in ms)")
        .help("Sets the time to scan for a datamatrix")
        .required(true)
        .takes_value(true))
    .arg(Arg::with_name("barcode")
        .short("b")
        .long("barcode")
        .help("Sets the program to search for code128 on datamatrix failed reads")
        .required(false)
        .takes_value(false))
    .get_matches();

    let starting_path = matches.value_of("start_dir").unwrap();
    let scan_time = matches.value_of("scan_time").unwrap();
    let include_barcodes = matches.is_present("barcode");   

    let start = Instant::now();

    let num_files = lib::run(starting_path, scan_time, include_barcodes);
    
    let end = start.elapsed();

    println!("\nCompleted... {} JPG/CR2 pairs handled in {:?}.", num_files, end);

    if num_files != 0 {
        println!("Average time per image: {:?}", end / num_files as u32);
    }
}

