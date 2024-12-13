import SwiftUI

struct FlashcardView: View {
    let word: Word // Replace `Word` with the actual type
    let showEnglishFirst: Bool
    @Binding var showingFront: Bool
    @State private var offset = CGSize.zero
    @State private var isOffScreen = false
    var onSwiped: (SwipeDirection) -> Void

    var body: some View {
        GeometryReader { geometry in
            ZStack {
                RoundedRectangle(cornerRadius: 15)
                    .fill(Color.white)
                    .shadow(radius: 10)

                Text(showingFront ? (showEnglishFirst ? word.english : word.portuguese) : (showEnglishFirst ? word.portuguese : word.english))
                    .font(.title)
                    .multilineTextAlignment(.center)
                    .padding()
                    .foregroundColor(.black)
            }
            .frame(width: min(geometry.size.width * 0.85, 300), height: min(geometry.size.height * 0.5, 400))
            .position(x: geometry.size.width / 2, y: geometry.size.height / 2)
            .offset(x: offset.width, y: offset.height)
            .rotationEffect(.degrees(Double(offset.width) / 20))
            .gesture(
                DragGesture()
                    .onChanged { gesture in
                        offset = gesture.translation
                    }
                    .onEnded { gesture in
                        if abs(offset.width) > geometry.size.width / 2 {
                            // Flicked or swiped completely off screen
                            isOffScreen = true
                            if offset.width < 0 {
                                onSwiped(.left) // Swiped left
                            } else {
                                onSwiped(.right) // Swiped right
                            }
                            resetPositionAfterSwipe()
                        } else {
                            // Snap back to center if not swiped far enough
                            resetPosition()
                        }
                    }
            )
            .onTapGesture {
                showingFront.toggle()
            }
            .animation(.spring(), value: offset)
        }
        .background(Color.clear)
    }

    private func resetPosition() {
        withAnimation {
            offset = .zero
        }
    }

    private func resetPositionAfterSwipe() {
        withAnimation {
            offset = CGSize(width: offset.width > 0 ? 1000 : -1000, height: offset.height)
        }
    }
}

enum SwipeDirection {
    case left
    case right
}
