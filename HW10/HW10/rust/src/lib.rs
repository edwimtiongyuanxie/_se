//! HW10 Rust Package Example

/// 回傳一句問候語
pub fn hello(name: &str) -> String {
    format!("Hello, {}! This is HW10 Rust package.", name)
}

/// 簡單加法
pub fn add(a: i32, b: i32) -> i32 {
    a + b
}

/// 用學號打招呼
pub fn greet_student(student_id: &str) -> String {
    format!("你好，同學 {}！歡迎完成第10週作業。", student_id)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_hello() {
        assert_eq!(hello("World"), "Hello, World! This is HW10 Rust package.");
    }

    #[test]
    fn test_add() {
        assert_eq!(add(2, 3), 5);
    }
}
