import SwiftUI

struct ChatView: View {
    @State private var messages: [Message] = []
    @State private var inputText: String = ""
    @State private var isSending: Bool = false

    var body: some View {
        VStack(spacing: 0) {
            ScrollViewReader { proxy in
                ScrollView {
                    LazyVStack(alignment: .leading, spacing: 12) {
                        ForEach(messages) { message in
                            HStack(alignment: .top) {
                                if message.role == "assistant" { Spacer().frame(width: 8) }
                                Text(message.content)
                                    .padding(12)
                                    .background(message.role == "user" ? Color.blue.opacity(0.15) : Color.gray.opacity(0.15))
                                    .cornerRadius(12)
                                    .frame(maxWidth: .infinity, alignment: message.role == "user" ? .trailing : .leading)
                                    .textSelection(.enabled)
                                if message.role == "user" { Spacer().frame(width: 8) }
                            }
                            .id(message.id)
                        }
                    }
                    .padding(12)
                }
                .onChange(of: messages.count) { _ in
                    if let last = messages.last { proxy.scrollTo(last.id, anchor: .bottom) }
                }
            }

            Divider()

            HStack {
                TextField("Type your message", text: $inputText, axis: .vertical)
                    .textFieldStyle(.roundedBorder)
                    .lineLimit(1...4)
                Button(action: sendMessage) {
                    if isSending {
                        ProgressView()
                    } else {
                        Text("Send")
                    }
                }
                .disabled(inputText.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty || isSending)
            }
            .padding(12)
        }
    }

    private func sendMessage() {
        let text = inputText.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !text.isEmpty else { return }
        inputText = ""
        isSending = true

        let userMsg = Message(role: "user", content: text)
        messages.append(userMsg)

        Task {
            do {
                let reply = try await callBackend(message: text)
                let aiMsg = Message(role: "assistant", content: reply)
                messages.append(aiMsg)
            } catch {
                messages.append(Message(role: "assistant", content: "Error: \(error.localizedDescription)"))
            }
            isSending = false
        }
    }

    private func callBackend(message: String) async throws -> String {
        guard let url = URL(string: "http://127.0.0.1:8000/chat") else { throw URLError(.badURL) }
        var req = URLRequest(url: url)
        req.httpMethod = "POST"
        req.setValue("application/json", forHTTPHeaderField: "Content-Type")

        let body: [String: Any] = [
            "message": message
        ]
        req.httpBody = try JSONSerialization.data(withJSONObject: body)

        let (data, resp) = try await URLSession.shared.data(for: req)
        guard let http = resp as? HTTPURLResponse, 200..<300 ~= http.statusCode else {
            throw URLError(.badServerResponse)
        }
        let dto = try JSONDecoder().decode(ChatResponseDTO.self, from: data)
        return dto.reply
    }
}

#Preview {
    ChatView()
} 