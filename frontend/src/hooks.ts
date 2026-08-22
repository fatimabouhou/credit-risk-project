import { useEffect, useState } from 'react'
import { humanizeError } from './api'

export interface AsyncState<T> {
  data: T | null
  loading: boolean
  error: string | null
}

/**
 * Charge les données d'un client depuis un service backend au montage du composant
 * (chaque page fetch les siennes). `fetcher` n'est volontairement pas dans les deps :
 * les appelants passent une closure inline, recréée à chaque rendu — seul `clientId`
 * doit déclencher un nouveau fetch.
 */
export function useClientData<T>(fetcher: (clientId: string) => Promise<T>, clientId: string): AsyncState<T> {
  const [state, setState] = useState<AsyncState<T>>({ data: null, loading: true, error: null })

  useEffect(() => {
    let cancelled = false
    setState({ data: null, loading: true, error: null })

    fetcher(clientId)
      .then((data) => { if (!cancelled) setState({ data, loading: false, error: null }) })
      .catch((error: unknown) => {
        if (!cancelled) setState({ data: null, loading: false, error: humanizeError(error) })
      })

    return () => { cancelled = true }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [clientId])

  return state
}
