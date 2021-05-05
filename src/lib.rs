use std::process::{Command};
use std::collections::HashMap;
use std::time::Instant;
use std::path::Path;
 
use chrono::{Datelike, Timelike, Utc};

extern crate glob;

use glob::glob;
use fancy_regex::Regex;

/// Ensure the passed in path is valid (exists and is a directory), will exit with code 1 on invalid
fn path_exists(path: &str) {
    println!("Checking the existence of passed in path...");
    let path_obj = Path::new(path);

    if !path_obj.exists() || !path_obj.is_dir() {
        println!("failed! The starting directory either doesn't exist in the filesystem or is not a directory: {}", path);
        println!("The program will now exit...");
        std::process::exit(1);
    } else {
        println!("passed!")
    }
}

/// Ensure the libraries / CLI utilities are installed on the system, will panic on failure
fn check_installations() {
    println!("Checking installations of dmtx-utils and zbar...");

    Command::new("dmtxread")
        .arg("--help")
        .output()
        .expect("dmtxread command failed to start. Please ensure dmtx-utils are installed in your system");

    // io::stdout().flush().ok().expect("Could not flush stdout");

    Command::new("zbarimg")
        .arg("--help")
        .output()
        .expect("zbarimg command failed to start. Please ensure zbar is installed in your system");

    // io::stdout().flush().ok().expect("Could not flush stdout");

    println!("passed!");
}

/// Returns nothing - checks installation of required libraries and the validity of
/// the passed in path argument
///
/// # Arguments
///
/// * `path` - A str filesystem path, the starting directory to scan images
fn sanity_checks(path: &str) {
    check_installations();
    path_exists(path);
}

/// Returns a string - the standardized name generated from the decoded data
///
/// # Arguments
///
/// * `decoded_data` - A str from the decoding process of either dmtxread or zbarimg
fn convert_decoded_to_name(decoded_data: &str) -> String {
    let re = Regex::new(r"(.*?)MGCL\s?[0-9]{7,8}").unwrap();

    let regex_ret = re.captures(&decoded_data).unwrap();

    let mut result = "";

    match regex_ret {
        Some(captures) => {
            match captures.get(0) {
                Some(group) => {
                    let decoded_vec = decoded_data.split_at(group.start());
                    // println!("{:?}", text.split_at(group.start()));
                    result = decoded_vec.1;
                },
                _ => ()
            }
        },
        _ => ()
    }

    // remove trailing, leading whitespace, 
    // newlines, replace spaces with _ and remove instances of CODE-128
    result
        .trim()
        .replace("\n", "")
        .replace(" ", "_")
        .replace("CODE-128:", "").to_string()
}

/// Returns a string - the stdout from 'dmtxread' utility, CLI program
///
/// # Arguments
///
/// * `path` - A str filesystem path, the location of the image to scan
/// * `scan_time` - Milliseconds (as str) allowed to scan before quitting
pub fn dmtxread(path: &str, scan_time: &str) -> String {
    let ms_time = format!("{}{}", "-m", scan_time);

    let output = Command::new("dmtxread")
        .arg("--stop-after=1")
        .arg(ms_time.as_str())
        .arg(path)
        .output()
        .expect("dmtxread command failed to start. Please ensure it is installed in your system");

    let mgcl_number = String::from(String::from_utf8_lossy(&output.stdout));

    println!("Raw extracted data: {}", mgcl_number.clone());

    match mgcl_number.as_str() {
        "" => return String::default(),
        _ => return mgcl_number,
    }
}

/// Returns a string - the stdout from 'zbarimg' utility, CLI program
///
/// # Arguments
///
/// * `path` - A str filesystem path, the location of the image to scan
pub fn zbarimg(path: &str) -> String {
    let output = Command::new("zbarimg")
        .arg(path)
        .output()
        .expect("zbarimg command failed to start. Please ensure it is installed in your system");

    let mgcl_number = String::from(String::from_utf8_lossy(&output.stdout));

    match mgcl_number.as_str() {
        "" => return String::default(),
        _ => return mgcl_number,
    }
}

/// Collect all JPG and jpg files at and below a starting directory
///
/// # Arguments
///
/// * `starting_path` - A str filesystem path, the location to start at
pub fn collect(starting_path: &str) -> Vec<std::path::PathBuf> {
    println!("Collecting files...");

    let start = Instant::now();

    let pattern_jpg_cap = format!("{}/**/*.JPG", starting_path);
    let pattern_jpg = format!("{}/**/*.jpg", starting_path);

    let  files_raw: Result<Vec<_>, _>  = glob(pattern_jpg_cap.as_str())
        .unwrap()
        .chain(glob(pattern_jpg.as_str()).unwrap())
        .collect();

    let mut files = match files_raw {
        Ok(v) => v,
        _ => std::vec::Vec::default()
    };

    let end = start.elapsed();

    println!("done!");

    if files.len() < 1 {
        println!("No files to collect...");
        return files;
    }

    files.sort_by(|a,b| a.as_os_str().cmp(b.as_os_str()));

    println!("Files collected in {:?}...\n", end);

    files
}

/// Renames multiple files to standardized name recieved from decoding datamatrix data.
/// Finds all images with the same name (e.g. IMG_1000) and renames them accordingly. This is
/// meant to find the corresponding CR2 images for a JPG.
///
/// # Arguments
///
/// * `base_path` - A String filesystem path, the location of the JPG
/// * `new_name` - A String of the standardized new name for the image
fn rename_all(base_path: String, new_name: String) -> Vec<(String, String)> {
    let raw_path = Path::new(base_path.as_str());
    let parent_path = raw_path.parent().unwrap();
    let old_name = raw_path.file_stem().unwrap();

    let pattern = format!("{}/{}.*", parent_path.to_str().unwrap(), old_name.to_str().unwrap());

    let files_raw: Result<Vec<_>, _>  = glob(pattern.as_str())
        .unwrap()
        .collect();

    let files = match files_raw {
        Ok(v) => v,
        _ => std::vec::Vec::default()
    };

    let mut edits: Vec<(String, String)> = Vec::new();

    for path_buffer in files {
        let ext = path_buffer.extension().unwrap();

        let old_path = path_buffer.to_str().unwrap().to_string();
        let new_path = parent_path
            .join(format!("{}.{}", new_name, ext.to_str().unwrap())).to_str().unwrap().to_string();

        std::fs::rename(old_path.as_str(), new_path.clone());   

        edits.push((old_path, new_path));
    }

    edits
}


/// Decode datamatrices and barcodes at and below given OS path starting point
///
/// # Arguments
///
/// * `starting_path` - A str filesystem path, the location to start at
/// * `scane_time` - A str representing the maximum time in ms to search for a datamatrix
/// * `include_barcodes` - A bool that will include barcode (zbar) attempts on failed dmtx decodes
/// 
/// # Returns usize - number of files handled
pub fn run(starting_path: &str, scan_time: &str, include_barcodes: bool) -> usize {
    sanity_checks(starting_path);
    
    let mut specimen: HashMap::<String, std::vec::Vec<String>> = HashMap::new();
    let mut edits: HashMap::<String, String> = HashMap::new();
    let mut failures: Vec<String> = Vec::new();

    let files = collect(starting_path);
    let ret = files.len();

    for path_buffer in files {
        println!("Attempting to extract datamatrix data from {}...", path_buffer.to_str().unwrap());


        let mut decoded_data = dmtxread(path_buffer.to_str().unwrap(), scan_time);

        if decoded_data == "" {
            println!("failed! (no datamatrix data could be extracted)\n");

            if include_barcodes {
                println!("Attempting to extract barcode data from {}...", path_buffer.to_str().unwrap());
        


                decoded_data = zbarimg(path_buffer.to_str().unwrap());

                if decoded_data == "" {
                    println!("failed! (no barcode data could be extracted)\n");
                    failures.push(path_buffer.to_str().unwrap().to_string());

                    continue;
                }
            } else {
                failures.push(path_buffer.to_str().unwrap().to_string());
                continue;
            }
        }

        let proper_name = convert_decoded_to_name(decoded_data.as_str());

        specimen.entry(proper_name.clone())
            .and_modify(|occurrences| {
                let suffix = match occurrences.len() {
                    1 => "_V",
                    _ => "_MANUAL"
                };

                let full_name = format!("{}{}", proper_name.clone(), suffix);

                println!("success!\nProper name determined to be: {}\n", full_name);

                for (old, new) in rename_all(path_buffer.to_str().unwrap().to_string(), full_name.clone()) {
                    edits.insert(old, new);
                }

                occurrences.push(path_buffer.to_str().unwrap().to_string())

            })
            .or_insert_with(|| {
                let full_name = format!("{}{}", proper_name.clone(), "_D");

                println!("success!\nProper name determined to be: {}\n", full_name);

                for (old, new) in rename_all(path_buffer.to_str().unwrap().to_string(), full_name.clone()) {
                    edits.insert(old, new);
                }

                vec![path_buffer.to_str().unwrap().to_string()]
            });
    }

    println!("All computations and renaming completed...\n");

    let now = Utc::now();
    let (_, year) = now.year_ce();

    let timestamp = format!("{}_{}_{}-{}:{}", year, now.month(), now.day(), now.hour(), now.minute());

    let parent_path = Path::new(starting_path).parent();
    let log_path = parent_path.unwrap().join(format!("DATA_MATRIX_LOG_{}.csv", timestamp));


    let mut wtr = csv::Writer::from_path(log_path.clone()).unwrap();
    wtr.write_record(&["Old Path", "New Path"]).expect("Uh oh, something went wrong with the CSV writing...");

    for (old, new) in edits {
        wtr.write_record(&[old.as_str(), new.as_str()]).expect("Uh oh, something went wrong with the CSV writing...");
    }

    wtr.flush().expect("Uh oh, something went wrong with the CSV writing...");

    println!("done!");

    println!("\nLog file can be found here: {}", log_path.as_os_str().to_str().unwrap());


    if ret != 0 {
        println!("\nThere were {} failed attempts at reading datamatrices / barcodes", failures.len());
        println!("Failure rate: {}", failures.len() as u32 / ret as u32);
    }

    ret

}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_pass() {
        assert_eq!(dmtxread("/Users/aaronleopold/Documents/museum/datamatrix/test_images/matrices/MGCL_1037779_D.JPG", "30000"), String::from("MGCL 1037795"));
    }

    #[test]
    fn test_fail() {
        assert_eq!(dmtxread("/Users/aaronleopold/Documents/museum/datamatrix/test_images/2d/IMG017.jpg", "30000"), String::from(""));
    }
}

