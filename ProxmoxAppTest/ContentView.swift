import SwiftUI

struct ContentView: View {
    @State private var connectionStatus = "Ainda não verificado"
    @State private var checking = false

    private let serverURL = URL(string: "https://termix.ncls.cc/")!

    var body: some View {
        NavigationStack {
            VStack(alignment: .leading, spacing: 24) {
                VStack(alignment: .leading, spacing: 8) {
                    Text("Distribuição iOS")
                        .font(.largeTitle.bold())
                    Text("Teste do ciclo de instalação e atualização pelo SideStore.")
                        .foregroundStyle(.secondary)
                }

                GroupBox("Aplicativo") {
                    LabeledContent("Versão", value: version)
                    LabeledContent("Build", value: build)
                }

                GroupBox("Servidor") {
                    VStack(alignment: .leading, spacing: 12) {
                        LabeledContent("Endereço", value: serverURL.host() ?? "")
                        Text(connectionStatus)
                            .foregroundStyle(.secondary)
                        Button {
                            Task { await checkConnection() }
                        } label: {
                            if checking {
                                ProgressView()
                            } else {
                                Label("Verificar conexão", systemImage: "network")
                            }
                        }
                        .buttonStyle(.borderedProminent)
                        .disabled(checking)
                    }
                }

                Spacer()
            }
            .padding(20)
            .navigationTitle("ProxmoxAppTest")
        }
    }

    private var version: String {
        Bundle.main.infoDictionary?["CFBundleShortVersionString"] as? String ?? "desconhecida"
    }

    private var build: String {
        Bundle.main.infoDictionary?["CFBundleVersion"] as? String ?? "desconhecido"
    }

    @MainActor
    private func checkConnection() async {
        checking = true
        defer { checking = false }
        do {
            var request = URLRequest(url: serverURL)
            request.httpMethod = "GET"
            request.timeoutInterval = 10
            let (_, response) = try await URLSession.shared.data(for: request)
            guard let http = response as? HTTPURLResponse else {
                connectionStatus = "Resposta inesperada do servidor"
                return
            }
            connectionStatus = (200..<400).contains(http.statusCode)
                ? "Servidor acessível (HTTP \(http.statusCode))"
                : "Servidor respondeu com HTTP \(http.statusCode)"
        } catch {
            connectionStatus = "Falha de conexão: \(error.localizedDescription)"
        }
    }
}
