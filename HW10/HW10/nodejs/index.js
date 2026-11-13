/**
 * HW10 Node.js Package Example
 */

function hello(name = "World") {
  return `Hello, ${name}! This is HW10 Node.js package.`;
}

function add(a, b) {
  return a + b;
}

function greetStudent(studentId) {
  return `你好，同學 ${studentId}！歡迎完成第10週作業。`;
}

module.exports = {
  hello,
  add,
  greetStudent
};
