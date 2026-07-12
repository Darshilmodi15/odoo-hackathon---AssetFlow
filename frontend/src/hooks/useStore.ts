import { useEffect, useState } from "react";
import { store } from "@/mocks/store";

export function useStore<T>(selector: () => T): T {
  store.refreshOperationalState();
  const [value, setValue] = useState<T>(selector);
  useEffect(() => {
    store.refreshOperationalState();
    setValue(selector());
    return store.subscribe(() => setValue(selector()));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);
  return value;
}
