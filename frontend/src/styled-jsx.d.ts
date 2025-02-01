declare module 'styled-jsx' {
  interface StyleJSXProps {
    jsx?: boolean;
    global?: boolean;
  }
}

declare global {
  namespace JSX {
    interface IntrinsicElements {
      style: React.DetailedHTMLProps<
        React.StyleHTMLAttributes<HTMLStyleElement> & { jsx?: boolean; global?: boolean },
        HTMLStyleElement
      >;
    }
  }
}
