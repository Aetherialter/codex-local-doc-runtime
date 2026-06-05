use pyo3::exceptions::PyValueError;
use pyo3::prelude::*;
use serde_json::json;
use sha2::{Digest, Sha256};
use std::fs::{canonicalize, metadata, File};
use std::io::{BufReader, Read};
use std::time::UNIX_EPOCH;

const VERSION: &str = "0.1.0";

#[pyfunction]
fn version() -> &'static str {
    VERSION
}

#[pyfunction]
fn sha256_file(path: &str) -> PyResult<String> {
    let file = File::open(path)?;
    let mut reader = BufReader::new(file);
    let mut hasher = Sha256::new();
    let mut buffer = [0_u8; 1024 * 64];

    loop {
        let read = reader.read(&mut buffer)?;
        if read == 0 {
            break;
        }
        hasher.update(&buffer[..read]);
    }

    Ok(format!("{:x}", hasher.finalize()))
}

#[pyfunction]
fn fingerprint(path: &str) -> PyResult<String> {
    let canonical = canonicalize(path)?;
    let meta = metadata(&canonical)?;
    let modified_ms = meta
        .modified()
        .ok()
        .and_then(|modified| modified.duration_since(UNIX_EPOCH).ok())
        .map(|duration| duration.as_millis())
        .unwrap_or_default();
    let digest = sha256_file(path)?;
    let value = json!({
        "absolute_path": normalize_slashes(&canonical.to_string_lossy()),
        "size": meta.len(),
        "mtime_ms": modified_ms,
        "sha256": digest,
        "backend": "rust",
    });
    Ok(value.to_string())
}

#[pyfunction]
fn is_path_within_root(root: &str, path: &str) -> PyResult<bool> {
    let root_path = match canonicalize(root) {
        Ok(value) => value,
        Err(_) => return Ok(false),
    };
    let target_path = match canonicalize(path) {
        Ok(value) => value,
        Err(_) => return Ok(false),
    };
    Ok(target_path.starts_with(root_path))
}

#[pyfunction]
fn normalize_slashes(path: &str) -> String {
    path.replace('\\', "/")
}

#[pyfunction]
fn validate_basic_json_object(json_text: &str) -> PyResult<bool> {
    let value: serde_json::Value = serde_json::from_str(json_text)
        .map_err(|exc| PyValueError::new_err(format!("Invalid JSON: {exc}")))?;
    if !value.is_object() {
        return Err(PyValueError::new_err("JSON root must be an object"));
    }
    Ok(true)
}

#[pymodule]
fn docrt_core(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(version, m)?)?;
    m.add_function(wrap_pyfunction!(sha256_file, m)?)?;
    m.add_function(wrap_pyfunction!(fingerprint, m)?)?;
    m.add_function(wrap_pyfunction!(is_path_within_root, m)?)?;
    m.add_function(wrap_pyfunction!(normalize_slashes, m)?)?;
    m.add_function(wrap_pyfunction!(validate_basic_json_object, m)?)?;
    Ok(())
}
