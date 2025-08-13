import Foundation

struct Message: Identifiable, Codable, Equatable {
    let id: UUID
    let role: String // "user" or "assistant"
    let content: String

    init(role: String, content: String) {
        self.id = UUID()
        self.role = role
        self.content = content
    }
} 