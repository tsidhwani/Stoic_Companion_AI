import SwiftUI

struct ScoreResponseDTO: Decodable {
    let medal: String
    let score: Int
    let explanation: String
    let principles: [String]?
    let model: String
}

struct PracticeView: View {
    @State private var problem: String = ""
    @State private var proposedResponse: String = ""
    @State private var isScoring: Bool = false
    @State private var result: ScoreResponseDTO?
    @State private var errorText: String?

    var body: some View {
        NavigationView {
            Form {
                Section(header: Text("Problem")) {
                    TextEditor(text: $problem)
                        .frame(minHeight: 100)
                }
                Section(header: Text("Your proposed Stoic response")) {
                    TextEditor(text: $proposedResponse)
                        .frame(minHeight: 120)
                }
                Section {
                    Button(action: scoreNow) {
                        if isScoring { ProgressView() } else { Text("Evaluate") }
                    }
                    .disabled(problem.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty || proposedResponse.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty || isScoring)
                }
                if let result = result {
                    Section(header: Text("Result")) {
                        HStack {
                            medalBadge(for: result.medal)
                            Text("\(result.medal.capitalized) · Score: \(result.score)")
                                .font(.headline)
                        }
                        Text(result.explanation)
                        if let principles = result.principles, !principles.isEmpty {
                            Text("\(principles.joined(separator: ", "))")
                                .foregroundColor(.secondary)
                        }
                    }
                }
                if let errorText = errorText {
                    Section {
                        Text(errorText).foregroundColor(.red)
                    }
                }
            }
            .navigationTitle("Practice")
        }
    }

    private func scoreNow() {
        result = nil
        errorText = nil
        isScoring = true
        Task {
            do {
                result = try await callScore(problem: problem, proposedResponse: proposedResponse)
            } catch {
                errorText = error.localizedDescription
            }
            isScoring = false
        }
    }

    private func callScore(problem: String, proposedResponse: String) async throws -> ScoreResponseDTO {
        guard let url = URL(string: "http://127.0.0.1:8000/score") else { throw URLError(.badURL) }
        var req = URLRequest(url: url)
        req.httpMethod = "POST"
        req.setValue("application/json", forHTTPHeaderField: "Content-Type")
        let body: [String: Any] = [
            "problem": problem,
            "proposed_response": proposedResponse
        ]
        req.httpBody = try JSONSerialization.data(withJSONObject: body)
        let (data, resp) = try await URLSession.shared.data(for: req)
        guard let http = resp as? HTTPURLResponse, 200..<300 ~= http.statusCode else {
            throw URLError(.badServerResponse)
        }
        return try JSONDecoder().decode(ScoreResponseDTO.self, from: data)
    }

    @ViewBuilder
    private func medalBadge(for medal: String) -> some View {
        let lower = medal.lowercased()
        let color: Color = {
            switch lower {
            case "gold": return .yellow
            case "silver": return .gray
            case "bronze": return .brown
            default: return .secondary
            }
        }()
        Circle()
            .fill(color.opacity(0.8))
            .frame(width: 16, height: 16)
    }
}

#Preview {
    PracticeView()
} 