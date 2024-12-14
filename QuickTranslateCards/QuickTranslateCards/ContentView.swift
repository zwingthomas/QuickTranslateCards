import SwiftUI

struct ContentView: View {
    @StateObject var manager = WordManager()
    @State private var currentWord: Word?
    @State private var offset: CGSize = .zero
    @State private var showingFront = true
    @State private var showKnownWords = false
    @State private var showEnglishFirst = true

    var body: some View {
        NavigationView {
            ZStack {
                LinearGradient(
                    gradient: Gradient(colors: [Color.blue.opacity(0.3), Color.purple.opacity(0.3)]),
                    startPoint: .topLeading,
                    endPoint: .bottomTrailing
                )
                .ignoresSafeArea()

                VStack(spacing: 20) {
                    ZStack {
                        if let word = currentWord {
                            FlashcardView(word: word,
                                          showEnglishFirst: showEnglishFirst,
                                          showingFront: $showingFront,
                                          onSwiped: handleSwipe)
                                .id(word.id) // Make SwiftUI recognize card changes
                                .offset(offset)
                                .animation(.spring(), value: offset)
                                .transition(.move(edge: .bottom)) // Transition from bottom
                                .gesture(
                                    DragGesture()
                                        .onChanged { value in
                                            offset = value.translation
                                        }
                                        .onEnded { value in
                                            let dragDistance = value.translation.width
                                            withAnimation {
                                                if dragDistance < -100 {
                                                    // Flicked left: known = 0
                                                    manager.updateWord(word, rating: 0)
                                                    dismissCardAndLoadNext()
                                                } else if dragDistance > 100 {
                                                    // Flicked right: not known = 9
                                                    manager.updateWord(word, rating: 9)
                                                    dismissCardAndLoadNext()
                                                } else {
                                                    // Not far enough, snap back
                                                    offset = .zero
                                                }
                                            }
                                        }
                                )
                        } else {
                            Text("No words available")
                                .font(.title)
                                .foregroundColor(.white)
                        }
                    }
                }
            }
            .toolbar {
                ToolbarItem(placement: .navigationBarTrailing) {
                    Menu {
                        Button("Known Words") {
                            showKnownWords = true
                        }
                        Button(action: toggleLanguage) {
                            Text(showEnglishFirst ? "Show in Portuguese" : "Show in English")
                        }
                    } label: {
                        Image(systemName: "ellipsis.circle")
                    }
                }
            }
            .sheet(isPresented: $showKnownWords) {
                KnownWordsView(manager: manager, showEnglishFirst: manager.showEnglishFirst)
            }
            .onAppear {
                loadNewCard()
            }
        }
    }

    func loadNewCard() {
        showingFront = true
        offset = .zero
        withAnimation {
            currentWord = manager.randomWord()
        }
    }

    func dismissCardAndLoadNext() {
        // Animate the current card off-screen before loading the next
        let direction = offset.width < 0 ? CGFloat(-1000) : CGFloat(1000)
        withAnimation {
            offset = CGSize(width: direction, height: offset.height)
        }

        // After a brief delay, load the next card with the transition
        DispatchQueue.main.asyncAfter(deadline: .now() + 0.3) {
            withAnimation {
                loadNewCard()
            }
        }
    }

    private func handleSwipe(direction: SwipeDirection) {
        guard let word = currentWord else { return }

        if direction == .left {
            // Mark as known (weight = 0)
            manager.updateWord(word, rating: 0)
        } else if direction == .right {
            // Mark as not known (weight = 9)
            manager.updateWord(word, rating: 9)
        }

        dismissCardAndLoadNext()
    }

    private func toggleLanguage() {
        showEnglishFirst.toggle()
    }
}
