import SwiftUI

struct ChatResponseDTO: Decodable {
    let reply: String
    let model: String
}

struct ContentView: View {
    var body: some View {
        TabView {
            ChatView()
                .tabItem { Label("Chat", systemImage: "bubble.left.and.bubble.right") }
            PracticeView()
                .tabItem { Label("Practice", systemImage: "graduationcap") }
        }
    }
}

#Preview {
    ContentView()
} 