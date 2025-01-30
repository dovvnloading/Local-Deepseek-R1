# Local-Deepseek-R1
Deepseek-Chat provides a modern desktop interface for local language models through Ollama. Built with PyQt5, it features persistent chat history, real-time model switching, and a clean dark theme UI. Perfect for users seeking a professional platform for local AI interactions. This was built literally over night so don't be too critical, its mostly just to give the community an alternative UI to use and hopefully create an environment of improving it too. 



![Screenshot 2025-01-30 104242_c](https://github.com/user-attachments/assets/75a816d0-6b15-45e7-8056-4bae24733ba8)
![Screenshot 2025-01-30 104242_b](https://github.com/user-attachments/assets/05ab7858-d6b9-46b3-aa2d-5018ae1fb7c1)
![Screenshot 2025-01-30 104242_a1](https://github.com/user-attachments/assets/11ae29ad-fe1a-498a-8b73-bae116cf84f5)
![Screenshot 2025-01-30 104242_a](https://github.com/user-attachments/assets/a00fe6a0-a845-4976-b41d-8e9f25a3bbb7)




## Overview

Deepseek-Chat is a PyQt5-based desktop application that provides a clean, intuitive interface for interacting with local language models through Ollama. Built with a focus on performance and user experience, it features persistent chat history, model switching, and a modern dark theme UI.

### Key Features

- 🚀 Clean, modern desktop interface
- 💾 Persistent chat history with local storage
- 🔄 Real-time model switching between Deepseek variants
- 🎨 Sleek dark theme with customized UI elements
- 📋 System tray integration for quick access
- 💭 Unique "thoughts" panel showing model reasoning
- 🖥️ Cross-platform compatibility

## Getting Started

### Prerequisites

- Python 3.8+
- Ollama installed and running
- Deepseek models pulled via Ollama

### Installation

1. Clone the repository:
```bash
git clone https://github.com/mattw/deepseek-chat.git
cd deepseek-chat
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run the application:
```bash
python main.py
```

## Technical Details

- Built with PyQt5 for robust desktop integration
- Uses WebEngine for enhanced chat display
- Implements custom styling and animations
- Features a modular architecture for easy expansion

---

# Contributing

Contributions to Deepseek-Chat of any scale are welcome! Here's how you can help:

### Priority Areas
- **Performance:** Chat history management and memory optimization
- **UI/UX:** Message rendering and search functionality
- **Testing:** Unit tests and integration testing
- **Documentation:** Code comments and user guides

### Getting Started
1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

Please ensure your PR description clearly describes the problem and solution. Include relevant issue numbers if applicable.

Report bugs by opening a new issue and include: steps to reproduce, expected behavior, actual behavior, and any relevant code samples.

---

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Author

**Matt Wesney** - *Main Developer*

## Acknowledgments

- Thanks to the Ollama team for making local LLMs accessible
- PyQt5 community for the robust framework
- All contributors who help improve this project


---




# Known Issues & Pitfalls

## Core Issues

1. **System Resource Management**
   - Memory usage isn't properly monitored or limited for chat history
   - No cleanup mechanism for old chat files and metadata
   - Large chat histories could impact performance

2. **Error Handling**
   - Ollama connection errors aren't gracefully handled
   - Network timeout scenarios need better management
   - Model loading failures lack proper user feedback

3. **State Management**
   - Duplicate handle_error() method implementations
   - Potential race conditions in chat history updates
   - Message history isn't properly synced between components

## UI/UX Concerns

1. **Chat Display**
   - No message loading indicators
   - Messages aren't paginated for large conversations
   - MathJax rendering can cause layout shifts

2. **Model Selection**
   - No validation of model availability before switching
   - Missing model download progress indicators
   - No feedback if selected model isn't installed

## Performance Opportunities

1. **Optimization Needs**
   - Chat history panel animation could be smoother
   - Message formatting is done synchronously
   - WebEngine view could be optimized for better performance

2. **Caching**
   - No caching mechanism for frequently used responses
   - Chat history loads entire conversation at once
   - Model switching doesn't preserve conversation context

## Security Considerations

1. **Data Security**
   - Chat data stored in plaintext
   - No encryption for persistent storage
   - No user authentication mechanism

## Future Improvements

1. **Critical Features**
   - Add chat export functionality
   - Implement conversation search
   - Add proper file attachment handling

2. **Code Structure**
   - Split large classes into smaller components
   - Implement proper dependency injection
   - Add comprehensive testing suite


---

# This project serves as a starting point for either beginners or anyone who wants to participate in making this better
