import { useEffect, useState } from "react";
import { store } from "@/mocks/store";

export function useStore<T>(selector: () => T): T {
  const [value, setValue] = useState<T>(selector);
  useEffect(() => {
    setValue(selector());
    return store.subscribe(() => setValue(selector()));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);
  return value;
}
