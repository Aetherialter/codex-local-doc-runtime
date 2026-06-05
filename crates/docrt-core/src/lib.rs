use pyo3::exceptions::PyValueError;
use pyo3::prelude::*;
use serde_json::json;
use serde_json::Value;
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
    let value = fingerprint_value(path)?;
    Ok(value.to_string())
}

#[pyfunction]
fn fingerprint_many(paths_json: &str) -> PyResult<String> {
    let paths: Vec<String> = serde_json::from_str(paths_json)
        .map_err(|exc| PyValueError::new_err(format!("Invalid paths JSON: {exc}")))?;
    let mut items = Vec::with_capacity(paths.len());
    for path in &paths {
        let mut value = fingerprint_value(path)?;
        if let Some(object) = value.as_object_mut() {
            object.insert("path".to_string(), json!(path));
        }
        items.push(value);
    }
    Ok(json!({
        "backend": "rust",
        "count": items.len(),
        "items": items,
    })
    .to_string())
}

fn fingerprint_value(path: &str) -> PyResult<Value> {
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
    Ok(value)
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

#[pyfunction]
fn plan_batch(paths_json: &str) -> PyResult<String> {
    let paths: Vec<String> = serde_json::from_str(paths_json)
        .map_err(|exc| PyValueError::new_err(format!("Invalid paths JSON: {exc}")))?;
    let planned: Vec<serde_json::Value> = paths
        .iter()
        .enumerate()
        .map(|(index, path)| {
            json!({
                "index": index,
                "path": path,
                "normalized_path": normalize_slashes(path),
            })
        })
        .collect();
    Ok(json!({
        "backend": "rust",
        "count": planned.len(),
        "items": planned,
    })
    .to_string())
}

#[pyfunction]
fn search_records(index_json: &str, query: &str, preview_size: usize) -> PyResult<String> {
    let data: Value = serde_json::from_str(index_json)
        .map_err(|exc| PyValueError::new_err(format!("Invalid index JSON: {exc}")))?;
    let records = data
        .get("records")
        .and_then(Value::as_array)
        .ok_or_else(|| PyValueError::new_err("Index JSON must contain a records array"))?;
    let query_lower = query.to_lowercase();
    let mut matches = Vec::new();
    for record in records {
        let text = record
            .get("text")
            .and_then(Value::as_str)
            .unwrap_or_default();
        if text.to_lowercase().contains(&query_lower) {
            matches.push(json!({
                "path": record.get("path").cloned().unwrap_or(Value::Null),
                "preview": preview(text, query, preview_size),
            }));
        }
    }
    Ok(json!({
        "backend": "rust",
        "query": query,
        "count": matches.len(),
        "matches": matches,
    })
    .to_string())
}

fn preview(text: &str, query: &str, size: usize) -> String {
    if size == 0 {
        return String::new();
    }
    let text_char_count = text.chars().count();
    if query.is_empty() {
        return text.chars().take(size).collect();
    }
    let text_lower = text.to_lowercase();
    let query_lower = query.to_lowercase();
    let Some(byte_position) = text_lower.find(&query_lower) else {
        return text.chars().take(size).collect();
    };
    let char_position = text_lower[..byte_position].chars().count();
    let query_chars = query_lower.chars().count();
    let start = char_position.saturating_sub(size / 2);
    let end = (char_position + query_chars + size / 2).min(text_char_count);
    text.chars().skip(start).take(end - start).collect()
}

#[pymodule]
fn docrt_core(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(version, m)?)?;
    m.add_function(wrap_pyfunction!(sha256_file, m)?)?;
    m.add_function(wrap_pyfunction!(fingerprint, m)?)?;
    m.add_function(wrap_pyfunction!(fingerprint_many, m)?)?;
    m.add_function(wrap_pyfunction!(is_path_within_root, m)?)?;
    m.add_function(wrap_pyfunction!(normalize_slashes, m)?)?;
    m.add_function(wrap_pyfunction!(validate_basic_json_object, m)?)?;
    m.add_function(wrap_pyfunction!(plan_batch, m)?)?;
    m.add_function(wrap_pyfunction!(search_records, m)?)?;
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn preview_returns_context_around_query() {
        let text = "alpha beta needle gamma delta";
        let result = preview(text, "needle", 14);
        assert!(result.contains("needle"));
        assert!(result.len() <= text.len());
    }

    #[test]
    fn search_records_returns_matches() {
        let payload = json!({
            "records": [
                {"path": "a.docx", "text": "hello needle world"},
                {"path": "b.docx", "text": "no match here"}
            ]
        })
        .to_string();

        let result = search_records(&payload, "needle", 20).expect("search should work");

        assert!(result.contains("\"backend\":\"rust\""));
        assert!(result.contains("a.docx"));
        assert!(!result.contains("b.docx"));
    }
}
