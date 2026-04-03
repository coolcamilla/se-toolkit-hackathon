-- Schema for the tutor question database
CREATE TABLE IF NOT EXISTS questions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    text TEXT NOT NULL,
    correct_answer TEXT NOT NULL,
    topic TEXT NOT NULL
);

-- Seed demo questions
INSERT OR IGNORE INTO questions (id, text, correct_answer, topic) VALUES
(1, 'What is recursion?', 'Recursion is a function calling itself until it reaches a base case', 'Algorithms'),
(2, 'What is Big O notation?', 'Big O describes the upper bound of an algorithm time complexity in the worst case', 'Algorithms'),
(3, 'What is the difference between stack and heap?', 'Stack is automatic memory for local variables, heap is dynamic memory for objects', 'Memory'),
(4, 'What does the HTTP GET method do?', 'GET requests data from a server without modifying it', 'Web'),
(5, 'What is the HTTP POST method?', 'POST sends data to a server to create a resource', 'Web'),
(6, 'What is a REST API?', 'REST is an architectural style for web services using HTTP methods and status codes', 'Web'),
(7, 'What is a hash table?', 'A hash table is a data structure that stores key-value pairs with average O(1) access', 'Data Structures'),
(8, 'What is a linked list?', 'A linked list is a linear structure where each element holds a reference to the next', 'Data Structures'),
(9, 'What is Docker?', 'Docker is a platform for containerizing applications, isolating the process and its dependencies', 'DevOps'),
(10, 'What is Git?', 'Git is a distributed version control system for tracking changes in source code', 'DevOps');
