import "@testing-library/jest-dom/vitest";

function createInMemoryStorage(): Storage {
  let values = new Map<string, string>();
  return {
    getItem(key: string): string | null {
      return values.has(key) ? values.get(key) ?? null : null;
    },
    setItem(key: string, value: string): void {
      values.set(key, value);
    },
    removeItem(key: string): void {
      values.delete(key);
    },
    clear(): void {
      values = new Map<string, string>();
    },
    key(index: number): string | null {
      const keys = Array.from(values.keys());
      return keys[index] ?? null;
    },
    get length(): number {
      return values.size;
    },
  };
}

Object.defineProperty(globalThis, "localStorage", {
  value: createInMemoryStorage(),
  configurable: true,
  writable: true,
});
